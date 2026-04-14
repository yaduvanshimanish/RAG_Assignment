import logging
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from sqlalchemy.orm import Session

from app.config import get_settings
from app.database import get_db
from app.models.models import Document, DocumentChunk
from app.schemas.schemas import ChunkResponse, DocumentDeleteResponse, DocumentListResponse, DocumentResponse
from app.services.document_processor import process_document
from app.services.faiss_service import get_faiss_service
from app.services.gemini_service import get_embeddings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/documents", tags=["Documents"])

ALLOWED_EXTENSIONS = {"pdf", "docx", "doc", "txt", "md"}

def utcnow():
    return datetime.now(timezone.utc)

@router.post("/upload", response_model=DocumentResponse, status_code=201)
def upload_document(file: UploadFile = File(...), db: Session = Depends(get_db)):
    settings = get_settings()
    
    if not file.filename:
        raise HTTPException(status_code=400, detail="Filename missing")
        
    ext = file.filename.split(".")[-1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail=f"Unsupported file extension: {ext}")
        
    ready_count = db.query(Document).filter(Document.status == "ready").count()
    if ready_count >= settings.MAX_DOCUMENTS:
        raise HTTPException(status_code=400, detail=f"Maximum number of ready documents ({settings.MAX_DOCUMENTS}) reached.")
        
    file_bytes = file.file.read()
    file_size = len(file_bytes)
    
    if file_size > settings.MAX_FILE_SIZE_MB * 1024 * 1024:
        raise HTTPException(status_code=400, detail=f"File exceeds maximum size of {settings.MAX_FILE_SIZE_MB}MB")
        
    unique_filename = f"{uuid.uuid4().hex}_{file.filename}"
    upload_dir = Path(settings.UPLOAD_DIR)
    upload_dir.mkdir(parents=True, exist_ok=True)
    
    file_path = upload_dir / unique_filename
    with open(file_path, "wb") as f:
        f.write(file_bytes)
        
    document = Document(
        filename=unique_filename,
        original_filename=file.filename,
        file_path=str(file_path),
        file_size=file_size,
        file_type=ext,
        status="processing"
    )
    db.add(document)
    db.commit()
    db.refresh(document)
    
    try:
        chunks_with_pages, total_pages = process_document(
            file_path=str(file_path),
            file_type=ext,
            chunk_size=settings.CHUNK_SIZE,
            chunk_overlap=settings.CHUNK_OVERLAP,
            max_pages=settings.MAX_PAGES_PER_DOC
        )
        
        if not chunks_with_pages:
            raise ValueError("No text extracted.")
            
        db_chunks = []
        for index, (text, page_number) in enumerate(chunks_with_pages):
            chunk = DocumentChunk(
                document_id=document.id,
                chunk_index=index,
                content=text,
                page_number=page_number
            )
            db.add(chunk)
            db_chunks.append(chunk)
            
        db.commit()
        for chunk in db_chunks:
            db.refresh(chunk)
            
        texts_to_embed = [c.content for c in db_chunks]
        embeddings = get_embeddings(texts_to_embed)
        
        chunk_db_ids = [c.id for c in db_chunks]
        faiss_service = get_faiss_service()
        faiss_ids = faiss_service.add_embeddings(embeddings, chunk_db_ids)
        
        for chunk, faiss_id in zip(db_chunks, faiss_ids):
            chunk.faiss_index_id = faiss_id
            
        document.total_pages = total_pages
        document.total_chunks = len(db_chunks)
        document.status = "ready"
        document.processed_at = utcnow()
        
        db.commit()
        db.refresh(document)
        
    except Exception as e:
        logger.error(f"Failed to process document {document.id}: {e}")
        document.status = "failed"
        document.error_message = str(e)
        db.commit()
        db.refresh(document)
        
    return document

@router.get("/", response_model=DocumentListResponse)
def list_documents(skip: int = 0, limit: int = 20, status: Optional[str] = Query(None), db: Session = Depends(get_db)):
    query = db.query(Document)
    if status is not None:
        query = query.filter(Document.status == status)
        
    total = query.count()
    documents = query.order_by(Document.uploaded_at.desc()).offset(skip).limit(limit).all()
    
    return {"total": total, "documents": documents}

@router.get("/{document_id}", response_model=DocumentResponse)
def get_document(document_id: int, db: Session = Depends(get_db)):
    document = db.query(Document).filter(Document.id == document_id).first()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    return document

@router.get("/{document_id}/chunks", response_model=List[ChunkResponse])
def get_document_chunks(document_id: int, skip: int = 0, limit: int = 50, db: Session = Depends(get_db)):
    document = db.query(Document).filter(Document.id == document_id).first()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
        
    chunks = db.query(DocumentChunk).filter(DocumentChunk.document_id == document_id).order_by(DocumentChunk.chunk_index).offset(skip).limit(limit).all()
    return chunks

@router.delete("/{document_id}", response_model=DocumentDeleteResponse)
def delete_document(document_id: int, db: Session = Depends(get_db)):
    document = db.query(Document).filter(Document.id == document_id).first()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
        
    chunks = db.query(DocumentChunk).filter(DocumentChunk.document_id == document_id).all()
    chunk_db_ids = [c.id for c in chunks]
    
    if chunk_db_ids:
        faiss_service = get_faiss_service()
        faiss_service.delete_by_chunk_ids(chunk_db_ids)
        
    file_path = Path(document.file_path)
    if file_path.exists():
        try:
            file_path.unlink()
        except Exception as e:
            logger.warning(f"Failed to delete file {file_path}: {e}")
    else:
        logger.warning(f"File {file_path} not found on disk during deletion")
        
    db.delete(document)
    db.commit()
    
    return {"message": "Document deleted successfully", "document_id": document_id}
