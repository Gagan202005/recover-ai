"""
RecoverAI — RAG: Embeddings
Google text-embedding-004 wrapper for generating embeddings.
"""

import google.generativeai as genai
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import settings

genai.configure(api_key=settings.google_api_key)

EMBEDDING_MODEL = "models/gemini-embedding-001"
EMBEDDING_DIMENSION = 3072


async def get_embedding(text: str) -> list:
    """Generate an embedding vector for a text string using Google's text-embedding-004."""
    result = genai.embed_content(model=EMBEDDING_MODEL, content=text)
    return result["embedding"]


async def get_embeddings_batch(texts: list) -> list:
    """Generate embeddings for a batch of texts."""
    results = []
    # Process in batches of 20 to avoid rate limits
    batch_size = 20
    for i in range(0, len(texts), batch_size):
        batch = texts[i:i + batch_size]
        for text in batch:
            result = genai.embed_content(model=EMBEDDING_MODEL, content=text)
            results.append(result["embedding"])
    return results
