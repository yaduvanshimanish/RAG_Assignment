import logging
import time
from typing import List, Optional
import google.generativeai as genai
from app.config import get_settings

logger = logging.getLogger(__name__)

def _configure_gemini() -> None:
    settings = get_settings()
    if not settings.GEMINI_API_KEY or settings.GEMINI_API_KEY == "your_gemini_api_key_here":
        raise ValueError("GEMINI_API_KEY is not set. Please configure it in .env")
    genai.configure(api_key=settings.GEMINI_API_KEY)

def get_embeddings(texts: List[str], batch_size: int = 20) -> List[List[float]]:
    _configure_gemini()
    settings = get_settings()
    all_embeddings = []
    
    for i in range(0, len(texts), batch_size):
        batch = texts[i:i + batch_size]
        try:
            logger.debug(f"Processing batch of {len(batch)} embeddings...")
            result = genai.embed_content(
                model=settings.GEMINI_EMBEDDING_MODEL,
                content=batch,
                task_type="retrieval_document"
            )
            
            embedding_data = result.get("embedding")
            if embedding_data and isinstance(embedding_data, list):
                if isinstance(embedding_data[0], list):
                    all_embeddings.extend(embedding_data)
                elif isinstance(embedding_data[0], (float, int)):
                    all_embeddings.append(embedding_data)
                    
            time.sleep(0.1)
        except Exception as e:
            logger.error(f"Error generating embeddings for batch starting at {i}: {e}")
            raise
            
    return all_embeddings

def get_query_embedding(query: str) -> List[float]:
    _configure_gemini()
    settings = get_settings()
    
    result = genai.embed_content(
        model=settings.GEMINI_EMBEDDING_MODEL,
        content=query,
        task_type="retrieval_query"
    )
    
    embedding_data = result.get("embedding")
    if embedding_data and isinstance(embedding_data, list):
        if isinstance(embedding_data[0], list):
            return embedding_data[0]
        return embedding_data
    return []

def generate_answer(query: str, context_chunks: List[str], source_filenames: Optional[List[str]] = None) -> str:
    _configure_gemini()
    settings = get_settings()
    
    context_text = ""
    for i, chunk in enumerate(context_chunks):
        context_text += f"[Chunk {i + 1}]\n{chunk}\n\n"
        
    sources_text = ""
    if source_filenames:
        seen = set()
        deduped_sources = []
        for s in source_filenames:
            if s not in seen:
                seen.add(s)
                deduped_sources.append(s)
        sources_text = ", ".join(deduped_sources)
        
    prompt = f"""Section 1: CONTEXT
{context_text}

Section 2: SOURCES
{sources_text if sources_text else "None provided"}

Section 3: QUESTION
{query}

Section 4: INSTRUCTIONS
- Answer only from the provided context.
- If the answer is not present in context, say exactly: "I could not find an answer in the provided documents."
- Be concise and accurate.
- Do not invent information.

Section 5: ANSWER:
"""
    model = genai.GenerativeModel(settings.GEMINI_MODEL)
    response = model.generate_content(prompt)
    return response.text.strip()
