# RAG Pipeline - Retrieval-Augmented Generation with FastAPI, Gemini Flash, and FAISS

A production-ready Retrieval-Augmented Generation (RAG) pipeline REST API using FastAPI.

## Architecture Overview

Client -> FastAPI -> Services
                 |-> document_processor (Text extraction and chunking)
                 |-> gemini_service (Embeddings and LLM Generation)
                 |-> faiss_service (Vector search)
                 |-> SQLite (Database and metadata)
                 |-> FAISS (Vector store)

## Tech Stack

| Component       | Technology                    |
|-----------------|-------------------------------|
| Web Framework   | FastAPI 0.115                 |
| LLM             | Google Gemini Flash 2.0       |
| Embeddings      | Google text-embedding-004     |
| Vector Search   | FAISS (IndexFlatIP, cosine)   |
| Metadata DB     | SQLite (SQLAlchemy ORM)       |
| Containerization| Docker + Docker Compose       |

## Prerequisites

- Python 3.11+
- Docker
- Docker Compose
- Gemini API key. Get a free key at https://aistudio.google.com/app/apikey

## Local Setup (Python)

1. Clone the repository and navigate into it:
   ```bash
   git clone <repository_url>
   cd rag-pipeline
   ```
2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Configure environment variables:
   ```bash
   cp .env.example .env
   ```
   Edit `.env` and insert your GEMINI_API_KEY.
5. Run the application:
   ```bash
   uvicorn app.main:app --reload
   ```

## Docker Setup

Configure environment variables:
```bash
cp .env.example .env
```
Edit `.env` to add your GEMINI_API_KEY.

Start the application:
```bash
docker compose up --build -d
```
Check running containers:
```bash
docker compose ps
```
View logs:
```bash
docker compose logs -f rag-api
```
Stop the application:
```bash
docker compose down
```

With Nginx rate-limiting proxy:
```bash
docker compose --profile with-nginx up --build -d
```

## Cloud Deployment (AWS / GCP / Azure)

1. Provision a VM (Ubuntu 22.04 recommended).
2. Install Docker and Docker Compose.
3. Clone the repository to the VM.
4. Configure the `.env` file with your API keys.
5. Run `docker compose up --build -d`
6. Open port 8000 in your security group / firewall rules to allow external access.

## API Reference

| Method | Path                              | Description                    |
|--------|-----------------------------------|--------------------------------|
| GET    | /                                 | Root info                      |
| GET    | /health                           | Health check                   |
| POST   | /api/v1/documents/upload          | Upload document                |
| GET    | /api/v1/documents/                | List documents                 |
| GET    | /api/v1/documents/{id}            | Get document metadata          |
| GET    | /api/v1/documents/{id}/chunks     | Get document chunks            |
| DELETE | /api/v1/documents/{id}            | Delete document                |
| POST   | /api/v1/query/                    | RAG query                      |
| GET    | /api/v1/query/history             | Query history                  |

## Example curl Commands

Upload a document:
```bash
curl -X POST http://localhost:8000/api/v1/documents/upload -F "file=@/path/to/doc.pdf"
```

Perform a query:
```bash
curl -X POST http://localhost:8000/api/v1/query/ \
     -H "Content-Type: application/json" \
     -d '{"query": "What is the main topic?", "top_k": 5}'
```

List documents:
```bash
curl http://localhost:8000/api/v1/documents/
```

## Running Tests

Install required dependencies:
```bash
pip install -r requirements.txt
```
Run all tests:
```bash
pytest
```
Run specific test files:
```bash
pytest tests/test_document_processor.py -v
pytest tests/test_faiss_service.py -v
```

## Configuration Reference

| Environment Variable   | Default Value                    | Description                                  |
|------------------------|----------------------------------|----------------------------------------------|
| GEMINI_API_KEY         | your_gemini_api_key_here         | Google Gemini API key                        |
| GEMINI_MODEL           | gemini-2.0-flash                 | LLM Model to generate answers                |
| GEMINI_EMBEDDING_MODEL | models/text-embedding-004        | Embedding model used                         |
| FAISS_DIMENSION        | 768                              | Vector dimensions                            |
| FAISS_INDEX_PATH       | ./data/faiss_index               | Path to store FAISS index on disk            |
| MAX_DOCUMENTS          | 20                               | Maximum number of documents allowed          |
| MAX_PAGES_PER_DOC      | 1000                             | Document page parsing limit                  |
| CHUNK_SIZE             | 500                              | Text chunk size in words                     |
| CHUNK_OVERLAP          | 50                               | Overlap between text chunks                  |
| MAX_RETRIEVED_CHUNKS   | 5                                | Default top_k context limit                  |
| MAX_FILE_SIZE_MB       | 100                              | Maximum allowed upload file size (MB)        |
| DATABASE_URL           | sqlite:///./data/rag_metadata.db | Database connection URI                      |
| UPLOAD_DIR             | ./data/uploads                   | Path to store uploaded files                 |
| DEBUG                  | false                            | Enable debug mode                            |

## Supported File Types

PDF, DOCX, DOC, TXT, MD

## Limitations

- Max 20 documents
- Max 1000 pages per document
- Max 100MB per file
- FAISS is in-memory + persisted locally (not distributed)

## License

MIT
