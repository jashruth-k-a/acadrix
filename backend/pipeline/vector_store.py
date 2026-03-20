import os
import faiss
import numpy as np
import pickle
import requests
import time

HF_API_TOKEN = os.getenv("HF_API_TOKEN")
HF_MODEL_URL = "https://api-inference.huggingface.co/pipeline/feature-extraction/sentence-transformers/all-MiniLM-L6-v2"

HEADERS = {"Authorization": f"Bearer {HF_API_TOKEN}"}


def get_embeddings(texts: list) -> np.ndarray:
    """Call HF Inference API to get embeddings. Retries if model is loading."""
    payload = {"inputs": texts, "options": {"wait_for_model": True}}

    for attempt in range(3):
        response = requests.post(HF_MODEL_URL, headers=HEADERS, json=payload)

        if response.status_code == 200:
            embeddings = np.array(response.json(), dtype=np.float32)
            # Handle nested list from HF API
            if embeddings.ndim == 3:
                embeddings = embeddings.mean(axis=1)
            return embeddings

        elif response.status_code == 503:
            # Model is loading on HF side, wait and retry
            wait = response.json().get("estimated_time", 20)
            print(f"Model loading on HF, waiting {wait}s...")
            time.sleep(min(wait, 30))

        else:
            raise Exception(f"HF API error {response.status_code}: {response.text}")

    raise Exception("HF API failed after 3 attempts")


def create_embeddings(chunks):
    """Generate embeddings for a list of chunk dicts."""
    texts = [chunk["text"] for chunk in chunks]
    embeddings = get_embeddings(texts)
    return embeddings, chunks


def build_faiss_index(embeddings):
    """Build a FAISS flat L2 index from embedding array."""
    dimension = embeddings.shape[1]
    index = faiss.IndexFlatL2(dimension)
    index.add(np.array(embeddings, dtype=np.float32))
    return index


def save_index(index, chunks, index_path: str):
    """Save FAISS index and chunks to a specific path."""
    os.makedirs(index_path, exist_ok=True)
    faiss.write_index(index, os.path.join(index_path, "faiss_index.bin"))
    with open(os.path.join(index_path, "chunks.pkl"), "wb") as f:
        pickle.dump(chunks, f)


def load_index(index_path: str):
    """Load FAISS index and chunk metadata."""
    index = faiss.read_index(os.path.join(index_path, "faiss_index.bin"))
    with open(os.path.join(index_path, "chunks.pkl"), "rb") as f:
        chunks = pickle.load(f)
    return index, chunks


def index_exists(index_path: str) -> bool:
    """Check if a FAISS index exists."""
    return (
        os.path.exists(os.path.join(index_path, "faiss_index.bin")) and
        os.path.exists(os.path.join(index_path, "chunks.pkl"))
    )


def search_index(question: str, index_path: str, top_k: int = 5):
    """Embed question and retrieve top_k relevant chunks."""
    if not index_exists(index_path):
        return []

    index, chunks = load_index(index_path)
    question_embedding = get_embeddings([question])
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
    """Search across multiple document indexes."""
    all_results = []
    for path in index_paths:
        results = search_index(question, path, top_k=top_k)
        all_results.extend(results)

    all_results.sort(key=lambda x: x.get("score", float("inf")))
    return all_results[:top_k]