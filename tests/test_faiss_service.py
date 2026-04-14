import tempfile
import pytest

from app.services.faiss_service import FAISSService
from app.config import get_settings

@pytest.fixture(autouse=True)
def _patch_settings(monkeypatch):
    """Patch settings with a dimension of 4 for small, fast tests."""
    monkeypatch.setattr("app.services.faiss_service.get_settings", 
                        lambda: get_settings().model_copy(update={"FAISS_DIMENSION": 4}))

def test_create_new_index(monkeypatch):
    """Create FAISSService with temp dir. Verify index starts at 0 vectors."""
    with tempfile.TemporaryDirectory() as tmpdir:
        monkeypatch.setattr("app.services.faiss_service.get_settings", 
                            lambda: get_settings().model_copy(update={"FAISS_INDEX_PATH": tmpdir, "FAISS_DIMENSION": 4}))
        service = FAISSService()
        assert service.get_total_vectors() == 0

def test_add_and_total(monkeypatch):
    """Add 3 vectors of dim=4. Verify get_total_vectors() returns 3."""
    with tempfile.TemporaryDirectory() as tmpdir:
        monkeypatch.setattr("app.services.faiss_service.get_settings", 
                            lambda: get_settings().model_copy(update={"FAISS_INDEX_PATH": tmpdir, "FAISS_DIMENSION": 4}))
        service = FAISSService()
        vectors = [[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, 0]]
        db_ids = [1, 2, 3]
        service.add_embeddings(vectors, db_ids)
        assert service.get_total_vectors() == 3

def test_search_returns_correct_db_id(monkeypatch):
    """Search with query [1,0,0,0]. Top result must have db_id=101."""
    with tempfile.TemporaryDirectory() as tmpdir:
        monkeypatch.setattr("app.services.faiss_service.get_settings", 
                            lambda: get_settings().model_copy(update={"FAISS_INDEX_PATH": tmpdir, "FAISS_DIMENSION": 4}))
        service = FAISSService()
        service.add_embeddings([[1.0, 0.0, 0.0, 0.0], [0.0, 1.0, 0.0, 0.0]], [101, 102])
        
        results = service.search([1.0, 0.0, 0.0, 0.0], top_k=1)
        assert len(results) == 1
        assert results[0][0] == 101

def test_search_top_k(monkeypatch):
    """Add 5 vectors. Search with top_k=3. Verify exactly 3 results returned."""
    with tempfile.TemporaryDirectory() as tmpdir:
        monkeypatch.setattr("app.services.faiss_service.get_settings", 
                            lambda: get_settings().model_copy(update={"FAISS_INDEX_PATH": tmpdir, "FAISS_DIMENSION": 4}))
        service = FAISSService()
        vectors = [[1,0,0,0], [0,1,0,0], [0,0,1,0], [0,0,0,1], [0.5,0.5,0,0]]
        service.add_embeddings(vectors, [1, 2, 3, 4, 5])
        
        results = service.search([1,0,0,0], top_k=3)
        assert len(results) == 3

def test_search_empty_index(monkeypatch):
    """Search on empty index. Verify empty list returned."""
    with tempfile.TemporaryDirectory() as tmpdir:
        monkeypatch.setattr("app.services.faiss_service.get_settings", 
                            lambda: get_settings().model_copy(update={"FAISS_INDEX_PATH": tmpdir, "FAISS_DIMENSION": 4}))
        service = FAISSService()
        results = service.search([1,0,0,0])
        assert results == []

def test_allowed_faiss_ids_filter(monkeypatch):
    """Search with allowed_faiss_ids=[faiss_id_for_db_id_2]. Verify only db_id=2 is returned."""
    with tempfile.TemporaryDirectory() as tmpdir:
        monkeypatch.setattr("app.services.faiss_service.get_settings", 
                            lambda: get_settings().model_copy(update={"FAISS_INDEX_PATH": tmpdir, "FAISS_DIMENSION": 4}))
        service = FAISSService()
        faiss_ids = service.add_embeddings([[1,0,0,0], [1,0,0,0], [1,0,0,0]], [1, 2, 3])
        results = service.search([1,0,0,0], allowed_faiss_ids=[faiss_ids[1]])
        assert len(results) == 1
        assert results[0][0] == 2

def test_delete_reduces_count(monkeypatch):
    """Delete db_id=20. Verify total is 2."""
    with tempfile.TemporaryDirectory() as tmpdir:
        monkeypatch.setattr("app.services.faiss_service.get_settings", 
                            lambda: get_settings().model_copy(update={"FAISS_INDEX_PATH": tmpdir, "FAISS_DIMENSION": 4}))
        service = FAISSService()
        service.add_embeddings([[1,0,0,0], [0,1,0,0], [0,0,1,0]], [10, 20, 30])
        
        service.delete_by_chunk_ids([20])
        assert service.get_total_vectors() == 2

def test_delete_removes_correct_vector(monkeypatch):
    """Add [1,0,0,0] db_id=1 and [0,1,0,0] db_id=2. Delete db_id=1. Verify search results."""
    with tempfile.TemporaryDirectory() as tmpdir:
        monkeypatch.setattr("app.services.faiss_service.get_settings", 
                            lambda: get_settings().model_copy(update={"FAISS_INDEX_PATH": tmpdir, "FAISS_DIMENSION": 4}))
        service = FAISSService()
        service.add_embeddings([[1,0,0,0], [0,1,0,0]], [1, 2])
        
        service.delete_by_chunk_ids([1])
        results = service.search([1,0,0,0])
        assert results[0][0] == 2

def test_persist_and_reload(monkeypatch):
    """Create a second FAISSService pointing to same temp dir. Verify count."""
    with tempfile.TemporaryDirectory() as tmpdir:
        monkeypatch.setattr("app.services.faiss_service.get_settings", 
                            lambda: get_settings().model_copy(update={"FAISS_INDEX_PATH": tmpdir, "FAISS_DIMENSION": 4}))
        service1 = FAISSService()
        service1.add_embeddings([[1,0,0,0], [0,1,0,0]], [1, 2])
        
        service2 = FAISSService()
        assert service2.get_total_vectors() == 2
