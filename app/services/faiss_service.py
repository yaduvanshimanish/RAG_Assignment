import json
import logging
from pathlib import Path
from typing import List, Tuple, Optional
import numpy as np
import faiss

from app.config import get_settings

logger = logging.getLogger(__name__)

class FAISSService:
    def __init__(self):
        settings = get_settings()
        self.dimension = settings.FAISS_DIMENSION
        self.index_path = settings.FAISS_INDEX_PATH
        
        index_dir = Path(self.index_path)
        index_dir.mkdir(parents=True, exist_ok=True)
        
        self.index_file = index_dir / "index.faiss"
        self.meta_file = index_dir / "meta.json"
        
        self.id_map: List[int] = []
        self._load_or_create()

    def _load_or_create(self):
        if self.index_file.exists() and self.meta_file.exists():
            self.index = faiss.read_index(str(self.index_file))
            with open(self.meta_file, "r") as f:
                self.id_map = json.load(f)
            logger.info(f"Loaded FAISS index with {self.index.ntotal} vectors.")
        else:
            self.index = faiss.IndexFlatIP(self.dimension)
            logger.info("Created new FAISS inner product index.")

    def _save(self):
        faiss.write_index(self.index, str(self.index_file))
        with open(self.meta_file, "w") as f:
            json.dump(self.id_map, f)

    def _normalize(self, vectors: np.ndarray) -> np.ndarray:
        norms = np.linalg.norm(vectors, axis=1, keepdims=True)
        norms[norms == 0] = 1
        return vectors / norms

    def add_embeddings(self, embeddings: List[List[float]], chunk_db_ids: List[int]) -> List[int]:
        if len(embeddings) != len(chunk_db_ids):
            raise ValueError("Number of embeddings must match number of chunk_db_ids")
            
        if not embeddings:
            return []
            
        vectors = np.array(embeddings, dtype=np.float32)
        vectors = self._normalize(vectors)
        
        start_id = len(self.id_map)
        self.index.add(vectors)
        self.id_map.extend(chunk_db_ids)
        self._save()
        
        added_count = len(embeddings)
        logger.info(f"Added {added_count} vectors to FAISS index. Total: {self.index.ntotal}")
        return list(range(start_id, start_id + added_count))

    def search(self, query_embedding: List[float], top_k: int = 5, allowed_faiss_ids: Optional[List[int]] = None) -> List[Tuple[int, float]]:
        if self.index.ntotal == 0:
            return []
            
        query_vector = np.array([query_embedding], dtype=np.float32)
        query_vector = self._normalize(query_vector)
        
        fetch_count = top_k * 10 if allowed_faiss_ids is not None else top_k
        fetch_count = min(fetch_count, self.index.ntotal)
        
        scores, indices = self.index.search(query_vector, fetch_count)
        
        results = []
        for score, faiss_id in zip(scores[0], indices[0]):
            if faiss_id == -1:
                continue
                
            if allowed_faiss_ids is not None and faiss_id not in allowed_faiss_ids:
                continue
                
            db_id = self.id_map[faiss_id]
            results.append((db_id, float(score)))
            
            if len(results) >= top_k:
                break
                
        return results

    def delete_by_chunk_ids(self, chunk_db_ids: List[int]):
        delete_set = set(chunk_db_ids)
        keep_indices = [i for i, db_id in enumerate(self.id_map) if db_id not in delete_set]
        
        if not keep_indices:
            self.index = faiss.IndexFlatIP(self.dimension)
            self.id_map = []
        else:
            kept_vectors = []
            for i in keep_indices:
                kept_vectors.append(self.index.reconstruct(i))
            
            reconstructed = np.vstack(kept_vectors)
            self.index = faiss.IndexFlatIP(self.dimension)
            self.id_map = [self.id_map[i] for i in keep_indices]
            self.index.add(reconstructed)
            
        self._save()
        logger.info(f"Deleted {len(delete_set)} max vectors. New total: {self.index.ntotal}")

    def get_total_vectors(self) -> int:
        return self.index.ntotal if self.index is not None else 0

_faiss_instance: Optional[FAISSService] = None

def get_faiss_service() -> FAISSService:
    global _faiss_instance
    if _faiss_instance is None:
        _faiss_instance = FAISSService()
    return _faiss_instance
