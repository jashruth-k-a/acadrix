from fastapi import APIRouter, Depends, HTTPException
from bson import ObjectId
from auth import get_current_user
from database import get_history_collection
from models import HistoryItem, HistoryListResponse

router = APIRouter(prefix="/history", tags=["History"])


def history_to_item(h: dict) -> HistoryItem:
    return HistoryItem(
        id=str(h["_id"]),
        user_id=h["user_id"],
        question=h["question"],
        answer=h["answer"],
        document_id=h.get("document_id"),
        sources=h.get("sources", []),
        created_at=h["created_at"],
    )


@router.get("/", response_model=HistoryListResponse)
async def get_history(
    limit: int = 20,
    current_user: dict = Depends(get_current_user),
):
    col = get_history_collection()
    cursor = col.find({"user_id": current_user["user_id"]}).sort("created_at", -1).limit(limit)
    items = [history_to_item(h) async for h in cursor]
    return HistoryListResponse(history=items, total=len(items))


@router.delete("/{history_id}", status_code=204)
async def delete_history_item(
    history_id: str,
    current_user: dict = Depends(get_current_user),
):
    col = get_history_collection()
    result = await col.delete_one({
        "_id": ObjectId(history_id),
        "user_id": current_user["user_id"]
    })
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="History item not found")


@router.delete("/", status_code=204)
async def clear_history(current_user: dict = Depends(get_current_user)):
    col = get_history_collection()
    await col.delete_many({"user_id": current_user["user_id"]})