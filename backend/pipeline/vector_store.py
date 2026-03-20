import os
import io
import faiss
import numpy as np
import pickle
import requests
import time
import tempfile

HF_API_TOKEN = os.getenv("HF_API_TOKEN")
HF_MODEL_URL = "https://router.huggingface.co/hf-inference/models/sentence-transformers/all-MiniLM-L6-v2/pipeline/feature-extraction"

HEADERS = {"Authorization": f"Bearer {HF_API_TOKEN}"}


def get_embeddings(texts: list) -> np.ndarray:
    """Call HF Inference API to get embeddings."""
    payload = {"inputs": texts, "options": {"wait_for_model": True}}

    for attempt in range(3):
        response = requests.post(HF_MODEL_URL, headers=HEADERS, json=payload)

        if response.status_code == 200:
            embeddings = np.array(response.json(), dtype=np.float32)
            if embeddings.ndim == 3:
                embeddings = embeddings.mean(axis=1)
            return embeddings

        elif response.status_code == 503:
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
    """Save FAISS index and chunks to local disk."""
    os.makedirs(index_path, exist_ok=True)
    faiss.write_index(index, os.path.join(index_path, "faiss_index.bin"))
    with open(os.path.join(index_path, "chunks.pkl"), "wb") as f:
        pickle.dump(chunks, f)


def load_index(index_path: str):
    """Load FAISS index and chunk metadata from local disk."""
    index = faiss.read_index(os.path.join(index_path, "faiss_index.bin"))
    with open(os.path.join(index_path, "chunks.pkl"), "rb") as f:
        chunks = pickle.load(f)
    return index, chunks


def index_exists(index_path: str) -> bool:
    """Check if a FAISS index exists on disk."""
    return (
        os.path.exists(os.path.join(index_path, "faiss_index.bin")) and
        os.path.exists(os.path.join(index_path, "chunks.pkl"))
    )


# ===== GRIDFS FUNCTIONS =====

async def save_index_to_gridfs(index, chunks, user_id: str, document_id: str):
    """Save FAISS index and chunks to MongoDB GridFS."""
    from database import get_fs
    fs = get_fs()

    with tempfile.NamedTemporaryFile(delete=False, suffix=".bin") as tmp:
        tmp_path = tmp.name

    faiss.write_index(index, tmp_path)
    with open(tmp_path, "rb") as f:
        index_bytes = f.read()
    os.remove(tmp_path)

    chunks_bytes = pickle.dumps(chunks)

    await delete_index_from_gridfs(user_id, document_id)

    index_filename = f"{user_id}_{document_id}_index"
    await fs.upload_from_stream(index_filename, io.BytesIO(index_bytes))

    chunks_filename = f"{user_id}_{document_id}_chunks"
    await fs.upload_from_stream(chunks_filename, io.BytesIO(chunks_bytes))


async def load_index_from_gridfs(user_id: str, document_id: str):
    """Load FAISS index and chunks from MongoDB GridFS."""
    from database import get_fs
    fs = get_fs()

    index_filename = f"{user_id}_{document_id}_index"
    index_stream = io.BytesIO()
    await fs.download_to_stream_by_name(index_filename, index_stream)
    index_stream.seek(0)

    with tempfile.NamedTemporaryFile(delete=False, suffix=".bin") as tmp:
        tmp.write(index_stream.read())
        tmp_path = tmp.name

    index = faiss.read_index(tmp_path)
    os.remove(tmp_path)

    chunks_filename = f"{user_id}_{document_id}_chunks"
    chunks_stream = io.BytesIO()
    await fs.download_to_stream_by_name(chunks_filename, chunks_stream)
    chunks_stream.seek(0)
    chunks = pickle.loads(chunks_stream.read())

    return index, chunks


async def delete_index_from_gridfs(user_id: str, document_id: str):
    """Delete FAISS index and chunks from GridFS."""
    from database import get_fs
    fs = get_fs()

    for suffix in ["_index", "_chunks"]:
        filename = f"{user_id}_{document_id}{suffix}"
        try:
            async for grid_out in fs.find({"filename": filename}):
                await fs.delete(grid_out._id)
        except Exception:
            pass


async def index_exists_in_gridfs(user_id: str, document_id: str) -> bool:
    """Check if index exists in GridFS."""
    from database import get_fs
    fs = get_fs()

    filename = f"{user_id}_{document_id}_index"
    async for _ in fs.find({"filename": filename}):
        return True
    return False