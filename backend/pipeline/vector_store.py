import os
import faiss
import numpy as np
import pickle
from sentence_transformers import SentenceTransformer

# Load once at module level
model = SentenceTransformer("all-MiniLM-L6-v2")


def create_embeddings(chunks):
    """Generate embeddings for a list of chunk dicts."""
    texts = [chunk["text"] for chunk in chunks]
    embeddings = model.encode(texts, show_progress_bar=False)
    return embeddings, chunks


def build_faiss_index(embeddings):
    """Build a FAISS flat L2 index from embedding array."""
    dimension = embeddings.shape[1]
    index = faiss.IndexFlatL2(dimension)
    index.add(np.array(embeddings, dtype=np.float32))
    return index


def save_index(index, chunks, index_path: str):
    """Save FAISS index and chunks to a specific path (per-document)."""
    os.makedirs(index_path, exist_ok=True)
    faiss.write_index(index, os.path.join(index_path, "faiss_index.bin"))
    with open(os.path.join(index_path, "chunks.pkl"), "wb") as f:
        pickle.dump(chunks, f)


def load_index(index_path: str):
    """Load FAISS index and chunk metadata from a specific path."""
    index = faiss.read_index(os.path.join(index_path, "faiss_index.bin"))
    with open(os.path.join(index_path, "chunks.pkl"), "rb") as f:
        chunks = pickle.load(f)
    return index, chunks


def index_exists(index_path: str) -> bool:
    """Check if a FAISS index exists at the given path."""
    return (
        os.path.exists(os.path.join(index_path, "faiss_index.bin")) and
        os.path.exists(os.path.join(index_path, "chunks.pkl"))
    )


def search_index(question: str, index_path: str, top_k: int = 5):
    """
    Embed a question and retrieve top_k most relevant chunks from a specific index.
    Returns list of chunk dicts with keys: file_name, chunk_index, text, score.
    """
    if not index_exists(index_path):
        return []

    index, chunks = load_index(index_path)
    question_embedding = model.encode([question])
    distances, indices = index.search(
        np.array(question_embedding, dtype=np.float32), top_k
    )

    results = []
    for i, idx in enumerate(indices[0]):
        if idx != -1:
            chunk = chunks[idx].copy()
            chunk["score"] = float(distances[0][i])
            results.append(chunk)

    return results


def search_multiple_indexes(question: str, index_paths: list, top_k: int = 5):
    """
    Search across multiple document indexes (all docs for a user).
    Merges and returns top_k results sorted by score.
    """
    all_results = []
    for path in index_paths:
        results = search_index(question, path, top_k=top_k)
        all_results.extend(results)

    # Sort by score ascending (lower L2 distance = more relevant)
    all_results.sort(key=lambda x: x.get("score", float("inf")))
    return all_results[:top_k]