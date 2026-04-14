from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Text, DateTime, Float, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base

def utcnow():
    return datetime.now(timezone.utc)

class Document(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary key=True, index=True)
    filename = Column(String(255), nullable=False)
    original_filename = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_size = Column(Integer, nullable=False)
    file_type = Column(String(50), nullable=False)
    total_pages = Column(Integer, default=0)
    total_chunks = Column(Integer, default=0)
    status = Column(String(50), default="processing")
    error_message = Column(Text, nullable=True)
    uploaded_at = Column(DateTime, default=utcnow)
    processed_at = Column(DateTime, nullable=True)

    chunks = relationship("DocumentChunk", back_populates="document", cascade="all, delete-orphan")

    def to_dict(self):
        return {
            "id": self.id,
            "filename": self.filename,
            "original_filename": self.original_filename,
            "file_path": self.file_path,
            "file_size": self.file_size,
            "file_type": self.file_type,
            "total_pages": self.total_pages,
            "total_chunks": self.total_chunks,
            "status": self.status,
            "error_message": self.error_message,
            "uploaded_at": self.uploaded_at,
            "processed_at": self.processed_at
        }

class DocumentChunk(Base):
    __tablename__ = "document_chunks"

    id = Column(Integer, primary key=True, index=True)
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=False)
    chunk_index = Column(Integer, nullable=False)
    content = Column(Text, nullable=False)
    page_number = Column(Integer, nullable=True)
    faiss_index_id = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=utcnow)

    document = relationship("Document", back_populates="chunks")

    def to_dict(self):
        return {
            "id": self.id,
            "document_id": self.document_id,
            "chunk_index": self.chunk_index,
            "content": self.content,
            "page_number": self.page_number,
            "faiss_index_id": self.faiss_index_id,
            "created_at": self.created_at
        }

class QueryLog(Base):
    __tablename__ = "query_logs"

    id = Column(Integer, primary key=True, index=True)
    query_text = Column(Text, nullable=False)
    response_text = Column(Text, nullable=True)
    retrieved_chunk_ids = Column(Text, nullable=True)
    processing_time_ms = Column(Float, nullable=True)
    created_at = Column(DateTime, default=utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "query_text": self.query_text,
            "response_text": self.response_text,
            "retrieved_chunk_ids": self.retrieved_chunk_ids,
            "processing_time_ms": self.processing_time_ms,
            "created_at": self.created_at
        }
