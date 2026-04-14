import os
import tempfile
from unittest.mock import MagicMock
import pytest
from fastapi.testclient import TestClient

from app.config import get_settings
from app.database import Base, get_db
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

@pytest.fixture(scope="session")
def client():
    """Setup FastAPI TestClient with temp DB and dirs, and yield it."""
    with tempfile.TemporaryDirectory() as temp_dir:
        db_url = f"sqlite:///{temp_dir}/test.db"
        
        get_settings.cache_clear()
        settings = get_settings()
        settings.DATABASE_URL = db_url
        settings.FAISS_INDEX_PATH = os.path.join(temp_dir, "faiss")
        settings.UPLOAD_DIR = os.path.join(temp_dir, "uploads")
        settings.GEMINI_API_KEY = "test-key"
        
        from app.main import app
        
        engine = create_engine(db_url, connect_args={"check_same_thread": False})
        TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        Base.metadata.create_all(bind=engine)
        
        def override_get_db():
            db = TestingSessionLocal()
            try:
                yield db
            finally:
                db.close()
                
        app.dependency_overrides[get_db] = override_get_db
        
        os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
        os.makedirs(settings.FAISS_INDEX_PATH, exist_ok=True)
        
        with TestClient(app) as c:
            yield c

@pytest.fixture
def mock_faiss(monkeypatch):
    """Mock get_faiss_service to return a MagicMock object."""
    mock_service = MagicMock()
    mock_service.add_embeddings.side_effect = lambda embeddings, db_ids: list(range(len(embeddings)))
    mock_service.get_total_vectors.return_value = 0
    
    monkeypatch.setattr("app.routers.documents.get_faiss_service", lambda: mock_service)
    monkeypatch.setattr("app.main.get_faiss_service", lambda: mock_service)
    return mock_service

@pytest.fixture
def mock_embeddings(monkeypatch):
    """Mock get_embeddings to return zero vectors."""
    def _mock_get_embeddings(texts, batch_size=20):
        return [[0.1] * 768 for _ in texts]
        
    monkeypatch.setattr("app.routers.documents.get_embeddings", _mock_get_embeddings)

def test_health_check(client, mock_faiss):
    """GET /health returns 200. Response has keys status, total_documents, total_chunks."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "total_documents" in data
    assert "total_chunks" in data

def test_root_endpoint(client):
    """GET / returns 200. Response has docs key."""
    response = client.get("/")
    assert response.status_code == 200
    assert "docs" in response.json()

def test_upload_unsupported_extension(client):
    """POST /api/v1/documents/upload with file test.exe. Expect 400."""
    file_content = b"dummy"
    files = [("files", ("test.exe", file_content, "application/octet-stream"))]
    response = client.post("/api/v1/documents/upload", files=files)
    assert response.status_code == 400
    assert "Unsupported" in response.json()["detail"]

def test_upload_txt_success(client, mock_faiss, mock_embeddings):
    """Mock embeddings and faiss. POST upload. Expect 201."""
    text_content = b"word " * 300
    files = [("files", ("test.txt", text_content, "text/plain"))]
    response = client.post("/api/v1/documents/upload", files=files)
    
    assert response.status_code == 201
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 1
    assert data[0]["original_filename"] == "test.txt"
    assert data[0]["status"] in ["ready", "failed"]

def test_list_documents_empty(client):
    """GET /api/v1/documents. Expect 200. Response has total and documents keys."""
    response = client.get("/api/v1/documents")
    assert response.status_code == 200
    data = response.json()
    assert "total" in data
    assert "documents" in data
    assert isinstance(data["documents"], list)

def test_list_documents_with_status_filter(client):
    """GET /api/v1/documents?status=ready. Expect 200."""
    response = client.get("/api/v1/documents?status=ready")
    assert response.status_code == 200

def test_get_document_not_found(client):
    """GET /api/v1/documents/99999. Expect 404."""
    response = client.get("/api/v1/documents/99999")
    assert response.status_code == 404

def test_delete_document_not_found(client):
    """DELETE /api/v1/documents/99999. Expect 404."""
    response = client.delete("/api/v1/documents/99999")
    assert response.status_code == 404

def test_get_chunks_not_found(client):
    """GET /api/v1/documents/99999/chunks. Expect 404."""
    response = client.get("/api/v1/documents/99999/chunks")
    assert response.status_code == 404
