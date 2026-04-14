from functools import lru_cache
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-2.0-flash"
    GEMINI_EMBEDDING_MODEL: str = "models/text-embedding-004"
    FAISS_DIMENSION: int = 768
    FAISS_INDEX_PATH: str = "./data/faiss_index"
    MAX_DOCUMENTS: int = 20
    MAX_PAGES_PER_DOC: int = 1000
    CHUNK_SIZE: int = 500
    CHUNK_OVERLAP: int = 50
    MAX_RETRIEVED_CHUNKS: int = 5
    MAX_FILE_SIZE_MB: int = 100
    DATABASE_URL: str = "sqlite:///./data/rag_metadata.db"
    UPLOAD_DIR: str = "./data/uploads"
    DEBUG: bool = False

    APP_NAME: str = "RAG Pipeline"
    APP_VERSION: str = "1.0.0"

    class Config:
        env_file = ".env"

@lru_cache
def get_settings() -> Settings:
    return Settings()
