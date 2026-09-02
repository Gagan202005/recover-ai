"""
RecoverAI — RAG: Document Ingestion Pipeline
Ingests error codes and compliance rules into Pinecone (run ONCE).
"""

import asyncio
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from rag.embeddings import get_embedding
from rag.pinecone_client import upsert_documents, ensure_index
from pinecone import Pinecone, ServerlessSpec
from config import settings


async def ingest_error_codes():
    """Ingest error codes into Pinecone 'error_codes' namespace."""
    data_path = os.path.join(os.path.dirname(__file__), "data", "error_codes.json")
    with open(data_path) as f:
        error_codes = json.load(f)

    print(f"🔄 Ingesting {len(error_codes)} error codes into Pinecone...")

    documents = []
    for ec in error_codes:
        content = f"Error Code: {ec['code']}. Meaning: {ec['meaning']}. Action: {ec['action']}. Bank: {ec['bank']}. Recoverability: {ec['recoverability']}"
        embedding = await get_embedding(content)
        documents.append({
            "id": f"ec_{ec['code'].replace(':', '_').replace('/', '_')}",
            "values": embedding,
            "metadata": {
                "content": content,
                "code": ec["code"],
                "bank": ec["bank"],
                "recoverability": ec["recoverability"],
            },
        })

    upsert_documents(documents, namespace="error_codes")
    print(f"✅ Ingested {len(documents)} error codes")


async def ingest_compliance_rules():
    """Ingest compliance rules into Pinecone 'compliance' namespace."""
    data_path = os.path.join(os.path.dirname(__file__), "data", "compliance_rules.json")
    with open(data_path) as f:
        rules = json.load(f)

    print(f"🔄 Ingesting {len(rules)} compliance rules into Pinecone...")

    documents = []
    for rule in rules:
        content = f"Rule: {rule['title']} ({rule['rule_id']}). Source: {rule['source']}. {rule['body']}"
        embedding = await get_embedding(content)
        documents.append({
            "id": f"rule_{rule['rule_id']}",
            "values": embedding,
            "metadata": {
                "content": content,
                "rule_id": rule["rule_id"],
                "source": rule["source"],
                "category": rule["category"],
            },
        })

    upsert_documents(documents, namespace="compliance")
    print(f"✅ Ingested {len(documents)} compliance rules")


async def create_pinecone_index():
    """Create the Pinecone index if it doesn't exist."""
    pc = Pinecone(api_key=settings.pinecone_api_key)
    existing = [idx.name for idx in pc.list_indexes()]

    if settings.pinecone_index_name not in existing:
        print(f"🔄 Creating Pinecone index '{settings.pinecone_index_name}'...")
        pc.create_index(
            name=settings.pinecone_index_name,
            dimension=3072,  # gemini-embedding-001 outputs 3072 dimensions
            metric="cosine",
            spec=ServerlessSpec(cloud="aws", region="us-east-1"),
        )
        print(f"✅ Created index '{settings.pinecone_index_name}'")
    else:
        print(f"✅ Index '{settings.pinecone_index_name}' already exists")


async def main():
    print("=" * 60)
    print("🧠 RecoverAI — RAG Ingestion Pipeline")
    print("=" * 60)

    await create_pinecone_index()
    await ingest_error_codes()
    await ingest_compliance_rules()

    print("\n✅ All documents ingested into Pinecone!")
    print("   Namespace 'error_codes': 24 documents")
    print("   Namespace 'compliance': 10 documents")
    print("   Namespace 'recovery_playbook': populated during batch run")
    print("   Namespace 'customer_context': populated during batch run")


if __name__ == "__main__":
    asyncio.run(main())
