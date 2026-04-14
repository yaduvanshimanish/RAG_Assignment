import json
import logging
import time
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.models import Document, DocumentChunk, QueryLog
from app.schemas.schemas import QueryHistoryResponse, QueryRequest, QueryResponse
from app.services.faiss_service import get_faiss_service
from app.services.gemini_service import generate_answer, get_query_embedding

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/query", tags=["Query"])

@router.post("", response_model=QueryResponse)
def query_documents(request: QueryRequest, db: Session = Depends(get_db)):
    start_time = time.time()
    
    ready_docs_count = db.query(Document).filter(Document.status == "ready").count()
    if ready_docs_count == 0:
        raise HTTPException(status_code=400, detail="No documents available. Upload documents first.")
        
    allowed_faiss_ids = None
    if request.document_ids is not None:
        docs = db.query(Document).filter(Document.id.in_(request.document_ids), Document.status == "ready").all()
        if not docs:
            raise HTTPException(status_code=404, detail="Requested documents not found or not ready.")
            
        chunks = db.query(DocumentChunk).filter(
            DocumentChunk.document_id.in_(request.document_ids),
            DocumentChunk.faiss_index_id.isnot(None)
        ).all()
        
        allowed_faiss_ids = [c.faiss_index_id for c in chunks]
        if not allowed_faiss_ids:
            raise HTTPException(status_code=400, detail="Requested documents have no indexed chunks.")
            
    try:
        query_embedding = get_query_embedding(request.query)
    except Exception as e:
        logger.error(f"Embedding generation failed: {e}")
        raise HTTPException(status_code=500, detail=f"Embedding generation failed: {e}")
        
    try:
        faiss_service = get_faiss_service()
        results = faiss_service.search(query_embedding, request.top_k, allowed_faiss_ids)
    except Exception as e:
        logger.error(f"Vector search failed: {e}")
        raise HTTPException(status_code=500, detail=f"Vector search failed: {e}")
        
    if not results:
        processing_time_ms = (time.time() - start_time) * 1000
        
        log_entry = QueryLog(
            query_text=request.query,
            response_text="I could not find any relevant information in the uploaded documents.",
            retrieved_chunk_ids="[]",
            processing_time_ms=processing_time_ms
        )
        db.add(log_entry)
        db.commit()
        
        return QueryResponse(
            query=request.query,
            answer="I could not find any relevant information in the uploaded documents.",
            retrieved_chunks=[],
            processing_time_ms=processing_time_ms,
            sources=[]
        )
        
    db_ids = [r[0] for r in results]
    scores = {r[0]: r[1] for r in results}
    
    chunks = db.query(DocumentChunk).filter(DocumentChunk.id.in_(db_ids)).all()
    chunk_map = {c.id: c for c in chunks}
    
    ordered_chunks = [chunk_map[db_id] for db_id in db_ids if db_id in chunk_map]
    
    doc_ids = list(set([c.document_id for c in ordered_chunks]))
    docs = db.query(Document).filter(Document.id.in_(doc_ids)).all()
    doc_map = {d.id: d.original_filename for d in docs}
    
    source_filenames = [doc_map.get(c.document_id, "Unknown File") for c in ordered_chunks]
    context_texts = [c.content for c in ordered_chunks]
    
    try:
        answer = generate_answer(request.query, context_texts, source_filenames)
    except Exception as e:
        logger.error(f"Answer generation failed: {e}")
        raise HTTPException(status_code=500, detail=f"Answer generation failed: {e}")
        
    processing_time_ms = (time.time() - start_time) * 1000
    
    retrieved_chunk_ids_json = json.dumps(db_ids)
    log_entry = QueryLog(
        query_text=request.query,
        response_text=answer,
        retrieved_chunk_ids=retrieved_chunk_ids_json,
        processing_time_ms=processing_time_ms
    )
    db.add(log_entry)
    db.commit()
    
    retrieved_chunks_response = []
    for c in ordered_chunks:
        c_dict = c.to_dict()
        c_dict["score"] = scores.get(c.id)
        retrieved_chunks_response.append(c_dict)
        
    return QueryResponse(
        query=request.query,
        answer=answer,
        retrieved_chunks=retrieved_chunks_response,
        processing_time_ms=processing_time_ms,
        sources=list(set(source_filenames))
    )

@router.get("/history", response_model=List[QueryHistoryResponse])
def get_query_history(skip: int = 0, limit: int = 20, db: Session = Depends(get_db)):
    logs = db.query(QueryLog).order_by(QueryLog.created_at.desc()).offset(skip).limit(limit).all()
    return logs
