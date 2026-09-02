"""
RecoverAI — API: Transactions
Transaction detail, audit trail, debates, and promise-to-pay endpoints.
"""

from fastapi import APIRouter
from database import supabase

router = APIRouter(prefix="/api/transactions", tags=["transactions"])


# ─── Static Sub-Routes (Must be defined BEFORE parameterized /{transaction_id}) ───

@router.post("/sync-razorpay-failures")
async def sync_razorpay_failures():
    """Fetch failed payments directly from Razorpay REST API, ingest into Supabase, and process through swarm."""
    from channels.razorpay_client import fetch_recent_failures
    from agents.swarm import process_transaction
    from database import get_customer
    import uuid
    from datetime import datetime

    failed_payments = fetch_recent_failures(count=30)
    ingested = []

    for p in failed_payments:
        payment_id = p.get("id", "")
        order_id = p.get("order_id", "")
        amount = p.get("amount", 299900)
        error_code = p.get("error_code", "GATEWAY_ERROR")
        error_desc = p.get("error_description", "Payment failed")
        error_source = p.get("error_source", "gateway")
        bank = p.get("bank", "HDFC")
        method = p.get("method", "card")

        # Determine failure reason
        desc_low = (error_desc or "").lower()
        if "expired" in desc_low:
            failure_reason = "card_expired"
        elif "insufficient" in desc_low or "balance" in desc_low:
            failure_reason = "insufficient_funds"
        elif "timeout" in desc_low:
            failure_reason = "network_timeout"
        else:
            failure_reason = "bank_decline"

        # Check if already in DB
        try:
            existing = None
            if payment_id:
                res = supabase.table("transactions").select("id").eq("razorpay_payment_id", payment_id).execute()
                existing = res.data
            elif order_id:
                res = supabase.table("transactions").select("id").eq("razorpay_order_id", order_id).execute()
                existing = res.data

            if not existing:
                txn_id = f"rzp_{payment_id}" if payment_id else f"live_rzp_{uuid.uuid4().hex[:6]}"
                txn = {
                    "id": txn_id,
                    "razorpay_order_id": order_id or f"order_{uuid.uuid4().hex[:8]}",
                    "razorpay_payment_id": payment_id,
                    "customer_id": "cust_001",
                    "amount": amount,
                    "product_name": p.get("description", "Online Order"),
                    "method": method,
                    "bank": bank,
                    "status": "failed",
                    "failure_reason": failure_reason,
                    "error_code": error_code,
                    "error_description": error_desc,
                    "error_source": error_source,
                    "recovery_status": "pending",
                    "is_live_demo": True,
                    "created_at": datetime.utcnow().isoformat(),
                }
                supabase.table("transactions").upsert(txn).execute()
                customer = await get_customer("cust_001") or {}
                
                # Run swarm on the new failure
                import asyncio
                asyncio.create_task(process_transaction(txn, customer, is_live=True))
                ingested.append(txn_id)
        except Exception as err:
            print(f"⚠️ Error processing sync for payment {payment_id}: {err}")

    return {
        "status": "ok",
        "total_failures_in_razorpay": len(failed_payments),
        "newly_ingested_count": len(ingested),
        "newly_ingested_ids": ingested,
    }


@router.get("/promises/all")
async def get_all_promises():
    """Get all active scheduled promise-to-pay records with joined customer and transaction details."""
    result = supabase.table("promise_to_pay") \
        .select("*, customers(name, phone, preferred_language), transactions(product_name, failure_reason, recovery_status)") \
        .eq("status", "promised") \
        .order("created_at", desc=True) \
        .limit(20) \
        .execute()
    return result.data or []


@router.delete("/promises/all")
async def delete_all_promises():
    """Delete all scheduled promise-to-pay reminders."""
    try:
        result = supabase.table("promise_to_pay").delete().neq("id", 0).execute()
        return {"status": "ok", "deleted_count": len(result.data or [])}
    except Exception as e:
        result = supabase.table("promise_to_pay").delete().gte("created_at", "1970-01-01").execute()
        return {"status": "ok", "deleted_count": len(result.data or [])}


@router.delete("/promises/{promise_id}")
async def delete_promise(promise_id: str):
    """Delete a specific promise-to-pay reminder by ID."""
    try:
        pid = int(promise_id) if promise_id.isdigit() else promise_id
        result = supabase.table("promise_to_pay").delete().eq("id", pid).execute()
        return {"status": "ok", "deleted_id": promise_id}
    except Exception as e:
        return {"status": "error", "message": str(e)}


@router.get("/reminders/due")
async def get_due_reminders():
    """Get all scheduled promise-to-pay reminders that are due."""
    from datetime import date
    today_str = date.today().isoformat()
    result = supabase.table("promise_to_pay") \
        .select("*, customers(*), transactions(*)") \
        .eq("status", "promised") \
        .lte("promise_date", today_str) \
        .execute()
    return {"due_count": len(result.data or []), "reminders": result.data or []}


@router.post("/reminders/dispatch")
async def dispatch_reminders_now():
    """Manually trigger dispatch of all active scheduled promise reminders immediately."""
    from simulation.reminder_scheduler import check_and_dispatch_due_reminders
    dispatched = await check_and_dispatch_due_reminders(force_all=True)
    return {"status": "ok", "dispatched_count": len(dispatched), "dispatched": dispatched}


# ─── Filtered Collection Route ───

@router.get("/")
async def list_transactions(status: str = None, recovery_status: str = None, limit: int = 100):
    """List transactions with optional filters."""
    query = supabase.table("transactions").select("*, customers(name, segment, preferred_language)")
    if status:
        query = query.eq("status", status)
    if recovery_status:
        query = query.eq("recovery_status", recovery_status)
    result = query.order("created_at", desc=True).limit(limit).execute()
    return result.data or []


# ─── Parameterized Routes /{transaction_id} ───

@router.get("/{transaction_id}")
async def get_transaction(transaction_id: str):
    """Get a single transaction with full details."""
    result = supabase.table("transactions") \
        .select("*, customers(*)") \
        .eq("id", transaction_id) \
        .single() \
        .execute()
    return result.data


@router.get("/{transaction_id}/audit-trail")
async def get_audit_trail(transaction_id: str):
    """Get the full agent audit trail for a transaction."""
    result = supabase.table("recovery_actions") \
        .select("*") \
        .eq("transaction_id", transaction_id) \
        .order("created_at", desc=False) \
        .execute()
    return result.data or []


@router.get("/{transaction_id}/debates")
async def get_debates(transaction_id: str):
    """Get agent debates for a transaction."""
    result = supabase.table("agent_debates") \
        .select("*") \
        .eq("transaction_id", transaction_id) \
        .order("created_at", desc=False) \
        .execute()
    return result.data or []


@router.get("/{transaction_id}/messages")
async def get_messages(transaction_id: str):
    """Get all channel messages sent for a transaction."""
    result = supabase.table("channel_messages") \
        .select("*") \
        .eq("transaction_id", transaction_id) \
        .order("created_at", desc=False) \
        .execute()
    return result.data or []


@router.get("/{transaction_id}/promises")
async def get_promises(transaction_id: str):
    """Get promise-to-pay records for a specific transaction."""
    result = supabase.table("promise_to_pay") \
        .select("*") \
        .eq("transaction_id", transaction_id) \
        .order("created_at", desc=False) \
        .execute()
    return result.data or []
