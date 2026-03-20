import io
import asyncio

async def save_index_to_gridfs(index, chunks, user_id: str, document_id: str):
    """Save FAISS index and chunks to MongoDB GridFS."""
    from database import get_fs
    fs = get_fs()

    # Serialize index to bytes
    index_bytes = io.BytesIO()
    faiss.write_index(index, faiss.PyCallbackIOWriter(index_bytes.write))
    
    # Actually use a temp file approach for faiss serialization
    import tempfile
    with tempfile.NamedTemporaryFile(delete=False, suffix=".bin") as tmp:
        tmp_path = tmp.name
    
    faiss.write_index(index, tmp_path)
    with open(tmp_path, "rb") as f:
        index_bytes = f.read()
    os.remove(tmp_path)

    # Serialize chunks to bytes
    chunks_bytes = pickle.dumps(chunks)

    # Delete old files if they exist
    await delete_index_from_gridfs(user_id, document_id)

    # Save index
    index_filename = f"{user_id}_{document_id}_index"
    await fs.upload_from_stream(index_filename, io.BytesIO(index_bytes))

    # Save chunks
    chunks_filename = f"{user_id}_{document_id}_chunks"
    await fs.upload_from_stream(chunks_filename, io.BytesIO(chunks_bytes))


async def load_index_from_gridfs(user_id: str, document_id: str):
    """Load FAISS index and chunks from MongoDB GridFS."""
    from database import get_fs
    fs = get_fs()

    import tempfile

    # Load index
    index_filename = f"{user_id}_{document_id}_index"
    index_stream = io.BytesIO()
    await fs.download_to_stream_by_name(index_filename, index_stream)
    index_stream.seek(0)

    with tempfile.NamedTemporaryFile(delete=False, suffix=".bin") as tmp:
        tmp.write(index_stream.read())
        tmp_path = tmp.name

    index = faiss.read_index(tmp_path)
    os.remove(tmp_path)

    # Load chunks
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