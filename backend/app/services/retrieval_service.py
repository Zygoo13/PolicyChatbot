import json
from pathlib import Path
from typing import Any, Dict, List, Optional

import faiss
import numpy as np
from sentence_transformers import SentenceTransformer

from app.schemas import SourceItem


BASE_DIR = Path(__file__).resolve().parent.parent
VECTORSTORE_DIR = BASE_DIR / "data" / "vectorstore"

INDEX_PATH = VECTORSTORE_DIR / "index.faiss"
METADATA_PATH = VECTORSTORE_DIR / "metadata.json"

EMBEDDING_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
DISTANCE_THRESHOLD = 3.0

_embedding_model: Optional[SentenceTransformer] = None
_faiss_index = None
_metadata: Optional[List[Dict[str, Any]]] = None


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

        with open(METADATA_PATH, "r", encoding="utf-8") as f:
            _metadata = json.load(f)

    return _metadata


def is_ready() -> bool:
    return INDEX_PATH.exists() and METADATA_PATH.exists()


def metadata_to_source_item(metadata: Dict[str, Any]) -> SourceItem:
    return SourceItem(
        file_name=metadata.get("file_name", "unknown"),
        title=metadata.get("title"),
        chunk_id=metadata.get("chunk_id"),
        content_preview=metadata.get("content_preview"),
        content=metadata.get("content"),
    )


def _embed_query(question: str) -> np.ndarray:
    model = _get_embedding_model()
    embedding = model.encode([question], convert_to_numpy=True)

    if embedding.dtype != np.float32:
        embedding = embedding.astype("float32")

    return embedding


def search_relevant_chunks(question: str, top_k: int = 3) -> List[SourceItem]:
    if not is_ready():
        return []

    index = _load_faiss_index()
    metadata_list = _load_metadata()

    query_vector = _embed_query(question)
    distances, indices = index.search(query_vector, top_k)

    print("DEBUG question:", question)
    print("DEBUG distances:", distances)
    print("DEBUG indices:", indices)

    results: List[SourceItem] = []

    for dist, idx in zip(distances[0], indices[0]):
        if idx == -1:
            continue

        if idx < 0 or idx >= len(metadata_list):
            continue

        if dist > 3.0:
            continue

        item_metadata = metadata_list[idx]
        results.append(metadata_to_source_item(item_metadata))

    return results


def build_context_from_sources(sources: List[SourceItem]) -> str:
    if not sources:
        return ""

    parts: List[str] = []

    for src in sources:
        title = src.title or src.file_name
        content = src.content or src.content_preview or ""

        if not content.strip():
            continue

        parts.append(f"[{title}]\n{content}")

    return "\n\n".join(parts)
