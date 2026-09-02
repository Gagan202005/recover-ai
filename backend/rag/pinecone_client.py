"""
RecoverAI — RAG: Pinecone Client
Vector search engine for the 4 knowledge bases.
Provides intelligent semantic search with context-aware queries for each agent.
"""

from pinecone import Pinecone
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import settings
from rag.embeddings import get_embedding


def get_pinecone_index():
    pc = Pinecone(api_key=settings.pinecone_api_key)
    return pc.Index(settings.pinecone_index_name)


index = None

def ensure_index():
    global index
    if index is None:
        index = get_pinecone_index()
    return index


async def query_knowledge_base(query: str, namespace: str, top_k: int = 5, filter_dict: dict = None) -> list:
    """Query a Pinecone namespace with semantic search. Returns top-k results with metadata."""
    idx = ensure_index()
    query_embedding = await get_embedding(query)

    kwargs = {
        "vector": query_embedding,
        "top_k": top_k,
        "namespace": namespace,
        "include_metadata": True,
    }
    if filter_dict:
        kwargs["filter"] = filter_dict

    results = idx.query(**kwargs)
    return [
        {
            "id": match["id"],
            "score": round(match["score"], 4),
            "content": match["metadata"].get("content", ""),
            "metadata": {k: v for k, v in match["metadata"].items() if k != "content"},
        }
        for match in results.get("matches", [])
    ]


async def query_error_codes(error_code: str, bank: str = None) -> list:
    """Search the error_codes knowledge base for diagnostician agent.
    Builds a rich query combining error code, bank, and failure context.
    Falls back to unfiltered search if bank-specific filter returns 0 results."""
    query = f"Razorpay payment error code {error_code}"
    if bank and bank != "unknown":
        query += f" from {bank} bank gateway"
    query += " diagnosis root cause recovery action"

    # Try with bank filter first for more relevant results
    if bank and bank != "unknown":
        results = await query_knowledge_base(query, namespace="error_codes", top_k=5, filter_dict={"bank": bank})
        if results:
            return results

    # Fallback: search without bank filter (generic error codes)
    return await query_knowledge_base(query, namespace="error_codes", top_k=5)


async def query_compliance(action_type: str, channel: str = "", failure_type: str = "", amount: int = 0) -> list:
    """Search the compliance knowledge base for compliance agent.
    Builds a contextual query based on channel, failure type, and action."""
    parts = ["Indian payment recovery compliance regulations"]
    if channel:
        parts.append(f"{channel} channel")
    if failure_type:
        parts.append(f"for {failure_type} failure")
    if amount > 0:
        parts.append(f"amount ₹{amount // 100}")
    parts.append("RBI TRAI consumer protection DND opt-out retry limit frequency cap")
    query = " ".join(parts)
    return await query_knowledge_base(query, namespace="compliance", top_k=5)


async def query_playbook(failure_type: str, amount: int = 0, segment: str = "", 
                          bank: str = "", channel: str = "", method: str = "") -> list:
    """Search the recovery playbook for strategist agent.
    Builds a rich query combining failure type, amount, segment, bank, and method."""
    parts = [f"Recovery strategy for {failure_type} payment failure"]
    if amount:
        amount_val = amount // 100
        if amount_val > 10000:
            parts.append(f"high-value ₹{amount_val}")
        elif amount_val > 1000:
            parts.append(f"medium-value ₹{amount_val}")
        else:
            parts.append(f"low-value ₹{amount_val}")
    if segment:
        parts.append(f"{segment} customer segment")
    if bank and bank != "unknown":
        parts.append(f"{bank} bank")
    if method and method != "unknown":
        parts.append(f"{method} payment method")
    if channel:
        parts.append(f"via {channel} channel")
    parts.append("successful recovery case")
    query = " ".join(parts)

    # Build filter for more relevant results
    filter_dict = {}
    if failure_type and failure_type != "unknown":
        filter_dict["failure_type"] = failure_type
    
    return await query_knowledge_base(
        query, namespace="recovery_playbook", top_k=5,
        filter_dict=filter_dict if filter_dict else None
    )


async def query_customer_context(customer_name: str, customer_id: str = "") -> list:
    """Search the customer context knowledge base for sentinel agent."""
    query = f"Customer {customer_name} payment history preferences behavior"
    if customer_id:
        query += f" ID {customer_id}"
    return await query_knowledge_base(query, namespace="customer_context", top_k=3)


def upsert_documents(documents: list, namespace: str):
    """Upsert documents into a Pinecone namespace. Each doc needs id, values, metadata."""
    idx = ensure_index()
    batch_size = 100
    for i in range(0, len(documents), batch_size):
        batch = documents[i:i + batch_size]
        idx.upsert(vectors=batch, namespace=namespace)
