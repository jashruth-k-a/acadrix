import os
import shutil
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from bson import ObjectId

from auth import get_current_user
from database import get_documents_collection
from models import DocumentOut, DocumentListResponse
from config import get_settings

settings = get_settings()

router = APIRouter(prefix="/documents", tags=["Documents"])

ALLOWED_EXTENSIONS = {".pdf", ".txt", ".pptx"}
MAX_FILE_SIZE = settings.max_file_size_mb * 1024 * 1024  # bytes


def get_index_path(user_id: str, document_id: str) -> str:
    """Per-document FAISS index path."""
    return os.path.join(settings.faiss_index_path, user_id, document_id)


def doc_to_out(doc: dict) -> DocumentOut:
    return DocumentOut(
        id=str(doc["_id"]),
        user_id=doc["user_id"],
        filename=doc["filename"],
        original_name=doc["original_name"],
        file_size=doc["file_size"],
        status=doc["status"],
        chunk_count=doc.get("chunk_count", 0),
        uploaded_at=doc["uploaded_at"],
    )


@router.post("/upload", response_model=DocumentOut, status_code=status.HTTP_201_CREATED)
async def upload_document(
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user),
):
    # Validate extension
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail=f"Unsupported file type: {ext}. Allowed: pdf, txt, pptx")

    # Read file bytes
    file_bytes = await file.read()
    if len(file_bytes) > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail=f"File too large. Max size: {settings.max_file_size_mb}MB")

    # Save to disk
    user_upload_dir = os.path.join(settings.upload_dir, current_user["user_id"])
    os.makedirs(user_upload_dir, exist_ok=True)

    now = datetime.now(timezone.utc)
    docs = get_documents_collection()

    # Insert doc record with "processing" status
    doc_record = {
        "user_id": current_user["user_id"],
        "filename": file.filename,
        "original_name": file.filename,
        "file_size": len(file_bytes),
        "extension": ext,
        "status": "processing",
        "chunk_count": 0,
        "uploaded_at": now,
    }
    result = await docs.insert_one(doc_record)
    document_id = str(result.inserted_id)

    # Save file to disk
    file_path = os.path.join(user_upload_dir, f"{document_id}{ext}")
    with open(file_path, "wb") as f:
        f.write(file_bytes)

    # Run ingestion pipeline
    try:
        from pipeline.ingest import extract_text_from_bytes
        from pipeline.embeddings import chunk_documents
        from pipeline.vector_store import create_embeddings, build_faiss_index, save_index

        text = extract_text_from_bytes(file_bytes, ext)
        documents = [{"file_name": file.filename, "text": text}]
        chunks = chunk_documents(documents)
        embeddings, chunks = create_embeddings(chunks)
        index = build_faiss_index(embeddings)

        index_path = get_index_path(current_user["user_id"], document_id)
        save_index(index, chunks, index_path)

        # Update status to ready
        await docs.update_one(
            {"_id": ObjectId(document_id)},
            {"$set": {"status": "ready", "chunk_count": len(chunks)}}
        )
        doc_record["status"] = "ready"
        doc_record["chunk_count"] = len(chunks)

    except Exception as e:
        await docs.update_one(
            {"_id": ObjectId(document_id)},
            {"$set": {"status": "failed"}}
        )
        doc_record["status"] = "failed"

    doc_record["_id"] = result.inserted_id
    return doc_to_out(doc_record)


@router.get("/", response_model=DocumentListResponse)
async def list_documents(current_user: dict = Depends(get_current_user)):
    docs = get_documents_collection()
    cursor = docs.find({"user_id": current_user["user_id"]}).sort("uploaded_at", -1)
    documents = [doc_to_out(doc) async for doc in cursor]
    return DocumentListResponse(documents=documents, total=len(documents))


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(
    document_id: str,
    current_user: dict = Depends(get_current_user),
):
    docs = get_documents_collection()
    doc = await docs.find_one({"_id": ObjectId(document_id), "user_id": current_user["user_id"]})
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    # Delete FAISS index from disk
    index_path = get_index_path(current_user["user_id"], document_id)
    if os.path.exists(index_path):
        shutil.rmtree(index_path)

    # Delete uploaded file
    ext = doc.get("extension", "")
    file_path = os.path.join(settings.upload_dir, current_user["user_id"], f"{document_id}{ext}")
    if os.path.exists(file_path):
        os.remove(file_path)

    await docs.delete_one({"_id": ObjectId(document_id)})