"""
RecoverAI — Database Client
Supabase Python client setup + helper functions.
"""

from supabase import create_client, Client
from config import settings

# Initialize Supabase client
supabase: Client = create_client(settings.supabase_url, settings.supabase_secret_key or settings.supabase_publishable_key)


# ─── Helper Functions ───────────────────────────────────────────

async def get_customer(customer_id: str) -> dict:
    """Fetch a single customer by ID."""
    result = supabase.table("customers").select("*").eq("id", customer_id).single().execute()
    return result.data


async def get_transaction(transaction_id: str) -> dict:
    """Fetch a single transaction by ID."""
    result = supabase.table("transactions").select("*").eq("id", transaction_id).single().execute()
    return result.data


async def get_failed_transactions(recovery_status: str = "pending") -> list:
    """Fetch all transactions with a given recovery status."""
    result = supabase.table("transactions") \
        .select("*") \
        .neq("status", "success") \
        .eq("recovery_status", recovery_status) \
        .order("created_at", desc=True) \
        .execute()
    return result.data


async def insert_recovery_action(action: dict) -> dict:
    """Insert an agent action into the audit trail."""
    result = supabase.table("recovery_actions").insert(action).execute()
    return result.data[0] if result.data else {}


async def insert_debate(debate: dict) -> dict:
    """Insert an agent debate record."""
    result = supabase.table("agent_debates").insert(debate).execute()
    return result.data[0] if result.data else {}


async def update_transaction(transaction_id: str, updates: dict) -> dict:
    """Update a transaction's fields."""
    result = supabase.table("transactions") \
        .update(updates) \
        .eq("id", transaction_id) \
        .execute()
    return result.data[0] if result.data else {}


async def insert_channel_message(message: dict) -> dict:
    """Log a sent message (WhatsApp/SMS/Email/Voice)."""
    result = supabase.table("channel_messages").insert(message).execute()
    return result.data[0] if result.data else {}


async def insert_promise(promise: dict) -> dict:
    """Insert a promise-to-pay record."""
    result = supabase.table("promise_to_pay").insert(promise).execute()
    return result.data[0] if result.data else {}


async def get_customer_messages_today(customer_id: str) -> int:
    """Count messages sent to a customer today (for rate limiting)."""
    from datetime import date
    today = date.today().isoformat()
    result = supabase.table("channel_messages") \
        .select("id", count="exact") \
        .eq("customer_id", customer_id) \
        .gte("created_at", f"{today}T00:00:00") \
        .execute()
    return result.count or 0


async def get_recent_failures_by_bank(bank: str, minutes: int = 30) -> list:
    """Fetch recent failures from a specific bank (for outage detection)."""
    from datetime import datetime, timedelta
    cutoff = (datetime.utcnow() - timedelta(minutes=minutes)).isoformat()
    result = supabase.table("transactions") \
        .select("*") \
        .eq("bank", bank) \
        .eq("status", "failed") \
        .gte("created_at", cutoff) \
        .execute()
    return result.data


async def get_dashboard_metrics() -> dict:
    """Calculate top-level dashboard metrics."""
    all_txns = supabase.table("transactions").select("*").neq("status", "success").execute()
    data = all_txns.data or []

    at_risk_amount = sum(t["amount"] for t in data)
    recovered = [t for t in data if t["recovery_status"] == "recovered"]
    recovered_amount = sum(t["recovery_amount"] or t["amount"] for t in recovered)
    processing = [t for t in data if t["recovery_status"] == "in_progress"]
    processing_amount = sum(t["amount"] for t in processing)
    exceptions = [t for t in data if t["recovery_status"] == "exception"]
    exception_amount = sum(t["amount"] for t in exceptions)

    return {
        "at_risk": {"count": len(data), "amount": at_risk_amount},
        "processing": {"count": len(processing), "amount": processing_amount},
        "recovered": {"count": len(recovered), "amount": recovered_amount},
        "exceptions": {"count": len(exceptions), "amount": exception_amount},
        "recovery_rate": round(len(recovered) / len(data) * 100, 1) if data else 0,
    }
