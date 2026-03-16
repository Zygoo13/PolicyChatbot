import json
import os
from pathlib import Path
from typing import List, Dict

import faiss
import numpy as np
from sentence_transformers import SentenceTransformer


BASE_DIR = Path(__file__).resolve().parent.parent
POLICIES_DIR = BASE_DIR / "data" / "policies"
VECTORSTORE_DIR = BASE_DIR / "data" / "vectorstore"

INDEX_PATH = VECTORSTORE_DIR / "index.faiss"
METADATA_PATH = VECTORSTORE_DIR / "metadata.json"

EMBEDDING_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"


def read_policy_files() -> List[Dict]:
    documents = []

    if not POLICIES_DIR.exists():
        raise FileNotFoundError(f"Policies directory not found: {POLICIES_DIR}")

    for file_path in POLICIES_DIR.glob("*.txt"):
        with open(file_path, "r", encoding="utf-8") as f:
            text = f.read().strip()

        documents.append(
            {
                "file_name": file_path.name,
                "text": text,
            }
        )

    return documents


def extract_title(text: str) -> str:
    for line in text.splitlines():
        line = line.strip()
        if line.startswith("TITLE:"):
            return line.replace("TITLE:", "").strip()
    return "Untitled"


def split_into_sections(text: str) -> List[Dict]:
    lines = text.splitlines()

    title = extract_title(text)
    chunks = []

    current_section = None
    current_content = []

    for line in lines:
        line = line.strip()

        if not line:
            continue

        if line.startswith("TITLE:"):
            continue

        if line.startswith("SECTION:"):
            if current_section and current_content:
                chunks.append(
                    {
                        "title": title,
                        "section": current_section,
                        "content": " ".join(current_content).strip(),
                    }
                )
            current_section = line.replace("SECTION:", "").strip()
            current_content = []
        else:
            current_content.append(line)

    if current_section and current_content:
        chunks.append(
            {
                "title": title,
                "section": current_section,
                "content": " ".join(current_content).strip(),
            }
        )

    return chunks


def build_chunks(documents: List[Dict]) -> List[Dict]:
    all_chunks = []

    for doc in documents:
        file_name = doc["file_name"]
        text = doc["text"]

        sections = split_into_sections(text)

        for idx, section in enumerate(sections):
            chunk_text = section["content"].strip()

            if not chunk_text:
                continue

            all_chunks.append(
                {
                    "chunk_id": f"{file_name}::chunk_{idx}",
                    "file_name": file_name,
                    "title": section["title"],
                    "section": section["section"],
                    "content": chunk_text,
                    "content_preview": chunk_text[:200],
                }
            )

    return all_chunks


def build_embeddings(texts: List[str]) -> np.ndarray:
    model = SentenceTransformer(EMBEDDING_MODEL_NAME)
    embeddings = model.encode(texts, convert_to_numpy=True, show_progress_bar=True)

    if embeddings.dtype != np.float32:
        embeddings = embeddings.astype("float32")

    return embeddings


def save_faiss_index(embeddings: np.ndarray) -> None:
    VECTORSTORE_DIR.mkdir(parents=True, exist_ok=True)

    dimension = embeddings.shape[1]
    index = faiss.IndexFlatL2(dimension)
    index.add(embeddings)

    faiss.write_index(index, str(INDEX_PATH))


def save_metadata(chunks: List[Dict]) -> None:
    with open(METADATA_PATH, "w", encoding="utf-8") as f:
        json.dump(chunks, f, ensure_ascii=False, indent=2)


def main():
    print("=== BUILD FAISS INDEX START ===")

    documents = read_policy_files()
    print(f"Loaded {len(documents)} policy files")

    chunks = build_chunks(documents)
    print(f"Built {len(chunks)} chunks")

    if not chunks:
        raise ValueError("No chunks were created. Please check your policy files.")

    texts = [chunk["content"] for chunk in chunks]

    embeddings = build_embeddings(texts)
    print(f"Embeddings shape: {embeddings.shape}")

    save_faiss_index(embeddings)
    save_metadata(chunks)

    print(f"Saved index to: {INDEX_PATH}")
    print(f"Saved metadata to: {METADATA_PATH}")
    print("=== BUILD FAISS INDEX DONE ===")


if __name__ == "__main__":
    main()
