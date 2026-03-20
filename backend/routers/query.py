from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
from bson import ObjectId

from auth import get_current_user
from database import get_documents_collection, get_history_collection
from models import QueryRequest, QueryResponse
from config import get_settings

settings = get_settings()
router = APIRouter(prefix="/query", tags=["Query"])


@router.post("/", response_model=QueryResponse)
async def query_documents(
    body: QueryRequest,
    current_user: dict = Depends(get_current_user),
):
    from pipeline.query import ask_acadrix
    from pipeline.vector_store import load_index_from_gridfs, index_exists_in_gridfs

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

        exists = await index_exists_in_gridfs(user_id, body.document_id)
        if not exists:
            raise HTTPException(status_code=404, detail="Index not found. Please re-upload the document.")

        index, chunks = await load_index_from_gridfs(user_id, body.document_id)
        result = ask_acadrix(
            body.question,
            index=index,
            chunks=chunks,
            mode=body.mode,
            top_k=body.top_k
        )

    # Query across all user documents
    else:
        cursor = docs_col.find({"user_id": user_id, "status": "ready"})
        ready_docs = [doc async for doc in cursor]

        if not ready_docs:
            raise HTTPException(
                status_code=400,
                detail="No ready documents found. Please upload and wait for processing."
            )

        all_chunks = []
        combined_index = None

        for doc in ready_docs:
            doc_id = str(doc["_id"])
            exists = await index_exists_in_gridfs(user_id, doc_id)
            if not exists:
                continue

            index, chunks = await load_index_from_gridfs(user_id, doc_id)
            all_chunks.extend(chunks)

            if combined_index is None:
                combined_index = index
            else:
                # Merge indexes
                import faiss
                import numpy as np
                vectors = np.zeros((index.ntotal, index.d), dtype=np.float32)
                index.reconstruct_n(0, index.ntotal, vectors)
                combined_index.add(vectors)

        if not all_chunks or combined_index is None:
            raise HTTPException(
                status_code=400,
                detail="No indexed documents found. Please re-upload your documents."
            )

        result = ask_acadrix(
            body.question,
            index=combined_index,
            chunks=all_chunks,
            mode=body.mode,
            top_k=body.top_k
        )

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