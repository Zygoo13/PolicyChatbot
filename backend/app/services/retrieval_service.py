import json
import re
import unicodedata
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import faiss
import numpy as np
from sentence_transformers import SentenceTransformer

from app.schemas import SourceItem


BASE_DIR = Path(__file__).resolve().parent.parent
VECTORSTORE_DIR = BASE_DIR / "data" / "vectorstore"

INDEX_PATH = VECTORSTORE_DIR / "index.faiss"
METADATA_PATH = VECTORSTORE_DIR / "metadata.json"

EMBEDDING_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
SIMILARITY_THRESHOLD = 0.25
DEFAULT_TOP_K = 3
RAW_CANDIDATE_K = 8

_embedding_model: Optional[SentenceTransformer] = None
_faiss_index = None
_metadata: Optional[List[Dict[str, Any]]] = None


def _normalize_text(text: str) -> str:
    text = text.lower().strip()
    text = unicodedata.normalize("NFKC", text)
    text = re.sub(r"\s+", " ", text)
    return text


def _get_embedding_model() -> SentenceTransformer:
    global _embedding_model

    if _embedding_model is None:
        _embedding_model = SentenceTransformer(EMBEDDING_MODEL_NAME)

    return _embedding_model


def _load_faiss_index():
    global _faiss_index

    if _faiss_index is None:
        if not INDEX_PATH.exists():
            raise FileNotFoundError(f"FAISS index not found: {INDEX_PATH}")
        _faiss_index = faiss.read_index(str(INDEX_PATH))

    return _faiss_index


def _load_metadata() -> List[Dict[str, Any]]:
    global _metadata

    if _metadata is None:
        if not METADATA_PATH.exists():
            raise FileNotFoundError(f"Metadata file not found: {METADATA_PATH}")

        with open(METADATA_PATH, "r", encoding="utf-8") as file:
            _metadata = json.load(file)

    return _metadata


def is_ready() -> bool:
    return INDEX_PATH.exists() and METADATA_PATH.exists()


def reset_cache() -> None:
    global _faiss_index, _metadata
    _faiss_index = None
    _metadata = None


def metadata_to_source_item(
    metadata: Dict[str, Any], score: Optional[float] = None
) -> SourceItem:
    return SourceItem(
        file_name=metadata.get("file_name", "unknown"),
        title=metadata.get("title"),
        section=metadata.get("section"),
        chunk_id=metadata.get("chunk_id"),
        content_preview=metadata.get("content_preview"),
        content=metadata.get("content"),
        score=score,
    )


def _embed_query(question: str) -> np.ndarray:
    model = _get_embedding_model()
    embedding = model.encode(
        [question],
        convert_to_numpy=True,
        normalize_embeddings=True,
    )

    if embedding.dtype != np.float32:
        embedding = embedding.astype("float32")

    return embedding


def _find_exact_section_matches(
    question: str, metadata_list: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    normalized_question = _normalize_text(question)
    matched = []

    for item in metadata_list:
        section = item.get("section", "")
        if not section:
            continue

        normalized_section = _normalize_text(section)

        if normalized_section in normalized_question:
            matched.append(item)

    return matched


def _keyword_overlap_score(question: str, metadata: Dict[str, Any]) -> int:
    q = set(_normalize_text(question).split())
    section = _normalize_text(metadata.get("section", ""))
    title = _normalize_text(metadata.get("title", ""))
    content = _normalize_text(metadata.get("content_preview", ""))

    tokens = set((section + " " + title + " " + content).split())
    return len(q & tokens)


def search_relevant_chunks(
    question: str, top_k: int = DEFAULT_TOP_K
) -> List[SourceItem]:
    if not is_ready():
        return []

    index = _load_faiss_index()
    metadata_list = _load_metadata()

    exact_matches = _find_exact_section_matches(question, metadata_list)
    if exact_matches:
        ranked_exact = sorted(
            exact_matches,
            key=lambda x: (
                -_keyword_overlap_score(question, x),
                x.get("section", ""),
            ),
        )
        return [
            metadata_to_source_item(item, score=1.0) for item in ranked_exact[:top_k]
        ]

    query_vector = _embed_query(question)
    scores, indices = index.search(query_vector, RAW_CANDIDATE_K)

    candidates: List[Tuple[float, Dict[str, Any]]] = []
    seen_chunk_ids = set()

    for score, idx in zip(scores[0], indices[0]):
        if idx == -1:
            continue

        if idx < 0 or idx >= len(metadata_list):
            continue

        if float(score) < SIMILARITY_THRESHOLD:
            continue

        item_metadata = metadata_list[idx]
        chunk_id = item_metadata.get("chunk_id")

        if chunk_id and chunk_id in seen_chunk_ids:
            continue

        if chunk_id:
            seen_chunk_ids.add(chunk_id)

        candidates.append((float(score), item_metadata))

    reranked = sorted(
        candidates,
        key=lambda x: (
            x[0] + 0.05 * _keyword_overlap_score(question, x[1]),
            (
                1
                if _normalize_text(x[1].get("section", "")) in _normalize_text(question)
                else 0
            ),
        ),
        reverse=True,
    )

    return [
        metadata_to_source_item(item, score=score) for score, item in reranked[:top_k]
    ]


def build_context_from_sources(sources: List[SourceItem]) -> str:
    if not sources:
        return ""

    parts: List[str] = []

    for src in sources:
        header_parts = []

        if src.title:
            header_parts.append(src.title)
        elif src.file_name:
            header_parts.append(src.file_name)

        if src.section:
            header_parts.append(src.section)

        header = " | ".join(header_parts).strip() or "Policy Context"
        content = (src.content or src.content_preview or "").strip()

        if not content:
            continue

        parts.append(f"[{header}]\n{content}")

    return "\n\n".join(parts)
