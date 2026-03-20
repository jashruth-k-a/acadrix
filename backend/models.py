from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from datetime import datetime


# ── Auth Models ────────────────────────────────────────────────────────────────

class UserRegister(BaseModel):
    name: str = Field(..., min_length=2, max_length=50)
    email: EmailStr
    password: str = Field(..., min_length=6)


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserOut(BaseModel):
    id: str
    name: str
    email: str
    created_at: datetime


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut


# ── Document Models ────────────────────────────────────────────────────────────

class DocumentOut(BaseModel):
    id: str
    user_id: str
    filename: str
    original_name: str
    file_size: int
    status: str                  # "processing" | "ready" | "failed"
    chunk_count: Optional[int] = 0
    uploaded_at: datetime


class DocumentListResponse(BaseModel):
    documents: List[DocumentOut]
    total: int


# ── Query Models ───────────────────────────────────────────────────────────────

class QueryRequest(BaseModel):
    question: str = Field(..., min_length=3, max_length=1000)
    document_id: Optional[str] = None   # None = query across all user docs
    top_k: Optional[int] = 5
    mode: Optional[str] = "direct" 


class QueryResponse(BaseModel):
    answer: str
    sources: List[dict]
    document_id: Optional[str]
    question: str
    
class HistoryMessage(BaseModel):
    role: str
    content: str

class QueryRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=1000)
    document_id: Optional[str] = None
    top_k: Optional[int] = 5
    mode: Optional[str] = "direct"
    history: Optional[List[HistoryMessage]] = []


# ── History Models ─────────────────────────────────────────────────────────────

class HistoryItem(BaseModel):
    id: str
    user_id: str
    question: str
    answer: str
    document_id: Optional[str]
    sources: List[dict]
    created_at: datetime


class HistoryListResponse(BaseModel):
    history: List[HistoryItem]
    total: int