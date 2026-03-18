import os
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
from bson import ObjectId

from auth import get_current_user
from database import get_documents_collection, get_history_collection
from models import QueryRequest, QueryResponse
from config import get_settings

settings = get_settings()
router = APIRouter(prefix="/query", tags=["Query"])


def get_index_path(user_id: str, document_id: str) -> str:
    return os.path.join(settings.faiss_index_path, user_id, document_id)


@router.post("/", response_model=QueryResponse)
async def query_documents(
    body: QueryRequest,
    current_user: dict = Depends(get_current_user),
):
    from pipeline.query import ask_acadrix

    docs_col = get_documents_collection()
    user_id = current_user["user_id"]

    # Single document query
    if body.document_id:
        doc = await docs_col.find_one({
            "_id": ObjectId(body.document_id),
            "user_id": user_id,
            "status": "ready"
        })
        if not doc:
            raise HTTPException(status_code=404, detail="Document not found or not ready")

        index_path = get_index_path(user_id, body.document_id)
        result = ask_acadrix(body.question, index_path=index_path, top_k=body.top_k, mode=body.mode)

    # Query across all user documents
    else:
        cursor = docs_col.find({"user_id": user_id, "status": "ready"})
        ready_docs = [doc async for doc in cursor]

        if not ready_docs:
            raise HTTPException(status_code=400, detail="No ready documents found. Please upload and wait for processing.")

        index_paths = [get_index_path(user_id, str(doc["_id"])) for doc in ready_docs]
        result = ask_acadrix(body.question, index_paths=index_paths, top_k=body.top_k, mode=body.mode)

    # Save to history
    history_col = get_history_collection()
    await history_col.insert_one({
        "user_id": user_id,
        "question": body.question,
        "answer": result["answer"],
        "document_id": body.document_id,
        "sources": result["sources"],
        "created_at": datetime.now(timezone.utc),
    })

    return QueryResponse(
        answer=result["answer"],
        sources=result["sources"],
        document_id=body.document_id,
        question=body.question,
    )