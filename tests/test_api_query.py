from unittest.mock import MagicMock
import pytest
import tempfile
import os

from fastapi.testclient import TestClient

from app.config import get_settings
from app.database import Base, get_db
from app.models.models import Document
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
    """Mock faiss_service logic."""
    mock_service = MagicMock()
    mock_service.search.return_value = []
    monkeypatch.setattr("app.routers.query.get_faiss_service", lambda: mock_service)
    
@pytest.fixture
def mock_gemini(monkeypatch):
    """Mock gemini service embedding and answer."""
    monkeypatch.setattr("app.routers.query.get_query_embedding", lambda q: [0.1] * 768)
    monkeypatch.setattr("app.routers.query.generate_answer", lambda q, c, s: "Mock answer")

def test_query_empty_body(client):
    """POST /api/v1/query/ with {}. Expect 422."""
    response = client.post("/api/v1/query", json={})
    assert response.status_code == 422

def test_query_empty_string(client):
    """POST /api/v1/query/ with empty query. Expect 422."""
    response = client.post("/api/v1/query", json={"query": "", "top_k": 3})
    assert response.status_code == 422

def test_query_no_documents(client):
    """POST /api/v1/query/ with valid query when no documents exist."""
    response = client.post("/api/v1/query", json={"query": "test query"})
    assert response.status_code == 400
    assert "No documents" in response.json()["detail"]

def test_query_invalid_top_k_zero(client):
    """POST /api/v1/query/ with top_k=0. Expect 422."""
    response = client.post("/api/v1/query", json={"query": "test", "top_k": 0})
    assert response.status_code == 422

def test_query_invalid_top_k_too_large(client):
    """POST /api/v1/query/ with top_k=100. Expect 422."""
    response = client.post("/api/v1/query", json={"query": "test", "top_k": 100})
    assert response.status_code == 422

def test_query_history_empty(client):
    """GET /api/v1/query/history. Expect 200."""
    response = client.get("/api/v1/query/history")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

def test_query_history_pagination(client):
    """GET /api/v1/query/history?skip=0&limit=5. Expect 200."""
    response = client.get("/api/v1/query/history?skip=0&limit=5")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

def test_query_nonexistent_document_ids(client, mock_faiss, mock_gemini):
    """POST /api/v1/query/ with document_ids=[99999]. Expect 404."""
    from app.main import app
    iterator = app.dependency_overrides[get_db]()
    db = next(iterator)
    dummy_doc = Document(filename="dummy", original_filename="dummy.txt", file_path="dummy", file_size=10, file_type="txt", status="ready")
    db.add(dummy_doc)
    db.commit()
    try:
        next(iterator)
    except StopIteration:
        pass
        
    response = client.post("/api/v1/query", json={"query": "test", "document_ids": [99999]})
    assert response.status_code == 404
