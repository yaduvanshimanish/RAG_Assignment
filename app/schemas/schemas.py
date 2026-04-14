from pydantic import BaseModel, ConfigDict, Field
from typing import List, Optional
from datetime import datetime

class DocumentResponse(BaseModel):
    id: int
    filename: str
    original_filename: str
    file_path: str
    file_size: int
    file_type: str
    total_pages: int
    total_chunks: int
    status: str
    error_message: Optional[str] = None
    uploaded_at: Optional[datetime] = None
    processed_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

class DocumentListResponse(BaseModel):
    total: int
    documents: List[DocumentResponse]

class DocumentDeleteResponse(BaseModel):
    message: str
    document_id: int

class ChunkResponse(BaseModel):
    id: int
    document_id: int
    chunk_index: int
    content: str
    page_number: Optional[int] = None
    score: Optional[float] = None

    model_config = ConfigDict(from_attributes=True)

class QueryRequest(BaseModel):
    query: str = Field(min_length=1, max_length=2000)
    top_k: int = Field(default=5, ge=1, le=20)
    document_ids: Optional[List[int]] = None

class QueryResponse(BaseModel):
    query: str
    answer: str
    retrieved_chunks: List[ChunkResponse]
    processing_time_ms: float
    sources: List[str]

class QueryHistoryResponse(BaseModel):
    id: int
    query_text: str
    response_text: Optional[str] = None
    processing_time_ms: Optional[float] = None
    created_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

class HealthResponse(BaseModel):
    status: str
    app_name: str
    version: str
    total_documents: int
    total_chunks: int
