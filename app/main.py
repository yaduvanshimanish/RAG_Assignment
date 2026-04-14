import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.database import SessionLocal, init_db
from app.models.models import Document, DocumentChunk
from app.routers import documents, query
from app.schemas.schemas import HealthResponse
from app.services.faiss_service import get_faiss_service

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s"
)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    
    Path(settings.UPLOAD_DIR).mkdir(parents=True, exist_ok=True)
    Path(settings.FAISS_INDEX_PATH).mkdir(parents=True, exist_ok=True)
    
    init_db()
    
    get_faiss_service()
    
    logger.info("Application startup complete.")
    yield
    logger.info("Application shutdown.")

settings = get_settings()

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="A Retrieval-Augmented Generation (RAG) pipeline REST API using FastAPI, Google Gemini Flash, and FAISS vector search.",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(documents.router, prefix="/api/v1")
app.include_router(query.router, prefix="/api/v1")

@app.get("/")
def read_root():
    settings = get_settings()
    return {
        "app_name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "docs": "/docs",
        "health": "/health"
    }

@app.get("/health", response_model=HealthResponse)
def health_check():
    settings = get_settings()
    db = SessionLocal()
    try:
        total_documents = db.query(Document).filter(Document.status == "ready").count()
        total_chunks = db.query(DocumentChunk).count()
        
        faiss_service = get_faiss_service()
        total_vectors = faiss_service.get_total_vectors()
        
        return HealthResponse(
            status="healthy",
            app_name=settings.APP_NAME,
            version=settings.APP_VERSION,
            total_documents=total_documents,
            total_chunks=total_chunks
        )
    finally:
        db.close()
