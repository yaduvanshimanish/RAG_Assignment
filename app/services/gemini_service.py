import logging
import time
from typing import List, Optional

from google import genai
from google.genai import types

from app.config import get_settings

logger = logging.getLogger(__name__)

# Module-level client, lazily initialized
_client: Optional[genai.Client] = None


def _get_client() -> genai.Client:
    """Return a configured Gemini client, creating it once per process."""
    global _client
    if _client is None:
        settings = get_settings()
        if not settings.GEMINI_API_KEY or settings.GEMINI_API_KEY == "your_gemini_api_key_here":
            raise ValueError("GEMINI_API_KEY is not set. Please configure it in .env")
        _client = genai.Client(api_key=settings.GEMINI_API_KEY)
    return _client


def get_embeddings(texts: List[str], batch_size: int = 20) -> List[List[float]]:
    """
    Generate embeddings for a list of texts using the Gemini embedding model.
    Processes in batches to stay within rate limits.
    Returns a list of embedding vectors (one per input text).
    """
    client = _get_client()
    settings = get_settings()
    all_embeddings: List[List[float]] = []

    for i in range(0, len(texts), batch_size):
        batch = texts[i:i + batch_size]
        try:
            logger.debug(f"Embedding batch {i // batch_size + 1}: {len(batch)} texts")
            response = client.models.embed_content(
                model=settings.GEMINI_EMBEDDING_MODEL,
                contents=batch,
                config=types.EmbedContentConfig(task_type="RETRIEVAL_DOCUMENT")
            )
            # The new SDK returns a list of Embedding objects under .embeddings
            for embedding_obj in response.embeddings:
                all_embeddings.append(embedding_obj.values)

            # Respect rate limits between batches
            time.sleep(0.1)
        except Exception as e:
            logger.error(f"Error generating embeddings for batch starting at index {i}: {e}")
            raise

    return all_embeddings


def get_query_embedding(query: str) -> List[float]:
    """
    Generate a single embedding for a user query.
    Uses RETRIEVAL_QUERY task type which is optimised for search queries.
    """
    client = _get_client()
    settings = get_settings()

    response = client.models.embed_content(
        model=settings.GEMINI_EMBEDDING_MODEL,
        contents=[query],
        config=types.EmbedContentConfig(task_type="RETRIEVAL_QUERY")
    )
    return response.embeddings[0].values


def generate_answer(
    query: str,
    context_chunks: List[str],
    source_filenames: Optional[List[str]] = None
) -> str:
    """
    Generate a grounded answer using the Gemini generative model.
    The prompt instructs the model to answer strictly from provided context.
    """
    client = _get_client()
    settings = get_settings()

    # Build numbered context block
    context_text = ""
    for i, chunk in enumerate(context_chunks):
        context_text += f"[Chunk {i + 1}]\n{chunk}\n\n"

    # Deduplicate source filenames
    sources_text = "None provided"
    if source_filenames:
        seen: set = set()
        deduped: List[str] = []
        for s in source_filenames:
            if s not in seen:
                seen.add(s)
                deduped.append(s)
        sources_text = ", ".join(deduped)

    prompt = f"""Section 1: CONTEXT
{context_text}
Section 2: SOURCES
{sources_text}

Section 3: QUESTION
{query}

Section 4: INSTRUCTIONS
- Answer only from the provided context.
- If the answer is not present in context, say exactly: "I could not find an answer in the provided documents."
- Be concise and accurate.
- Do not invent information.

Section 5: ANSWER:
"""

    response = client.models.generate_content(
        model=settings.GEMINI_MODEL,
        contents=prompt
    )
    return response.text.strip()
