Railway Backend Deployment Steps
---------------------------------

1. Install Railway CLI:
     npm install -g @railway/cli
     OR download from https://docs.railway.app/develop/cli

2. Login:
     railway login

3. Create a new project:
     railway init

4. Link this repository:
     railway link

5. Set environment variables in Railway dashboard:
     GEMINI_API_KEY = your key from aistudio.google.com
     GEMINI_MODEL = gemini-2.0-flash
     GEMINI_EMBEDDING_MODEL = models/text-embedding-004
     FAISS_DIMENSION = 768
     FAISS_INDEX_PATH = /app/data/faiss_index
     UPLOAD_DIR = /app/data/uploads
     DATABASE_URL = sqlite:////app/data/rag_metadata.db
     MAX_DOCUMENTS = 20
     CHUNK_SIZE = 500
     CHUNK_OVERLAP = 50

     Important: For production with persistent storage, add Railway Volume:
       - Go to your service -> Volumes -> Add Volume
       - Mount path: /app/data
       - This ensures uploaded documents and the FAISS index survive redeploys.

6. Deploy:
     railway up

7. Get your public URL:
     railway domain
     Example output: https://rag-pipeline-production.up.railway.app

8. Test the deployed backend:
     curl https://your-railway-url.up.railway.app/health
