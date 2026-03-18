from config import get_settings

settings = get_settings()

CHUNK_SIZE = 500        # you can tweak later
CHUNK_OVERLAP = 50


def chunk_text(text):
    """Split text into overlapping chunks."""
    chunks = []
    start = 0

    while start < len(text):
        end   = start + CHUNK_SIZE
        chunk = text[start:end]
        chunks.append(chunk)
        start += CHUNK_SIZE - CHUNK_OVERLAP

    return chunks


def chunk_documents(documents):
    """Convert full documents into chunked pieces, preserving source file name."""
    all_chunks = []

    for doc in documents:
        text_chunks = chunk_text(doc["text"])

        for i, chunk in enumerate(text_chunks):
            all_chunks.append({
                "file_name": doc["file_name"],
                "chunk_index": i,
                "text": chunk
            })

    return all_chunks
