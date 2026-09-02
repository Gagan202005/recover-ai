"""
RecoverAI — API: Simulation
Endpoints for triggering live demo scenarios and batch runs.
"""

import asyncio
from fastapi import APIRouter, BackgroundTasks
from database import supabase, get_customer
from simulation.live_scenarios import build_live_transaction, get_customer_override, SCENARIOS
from agents.swarm import process_transaction

router = APIRouter(prefix="/api/simulation", tags=["simulation"])


@router.get("/scenarios")
async def list_scenarios():
    """List available live demo scenarios."""
    return [{"key": k, "description": v["description"]} for k, v in SCENARIOS.items()]


@router.post("/create-checkout-order/{scenario_key}")
async def create_checkout_order(scenario_key: str):
    """Generate a live Razorpay order for opening the real checkout popup in frontend."""
    if scenario_key not in SCENARIOS:
        return {"error": f"Unknown scenario: {scenario_key}"}

    from channels.razorpay_client import create_order
    from config import settings

    txn = build_live_transaction(scenario_key)
    # Create real Razorpay order
    try:
        order = create_order(amount=txn["amount"], currency="INR", receipt=txn["id"][:30])
        if order and order.get("id"):
            txn["razorpay_order_id"] = order.get("id")
    except Exception as e:
        print(f"⚠️ Razorpay order creation warning: {e}")

    # Upsert transaction into Supabase
    supabase.table("transactions").upsert(txn).execute()

    customer = await get_customer("cust_001") or {}

    # Bug Fix #4: Return None instead of "" for order_id when Razorpay order creation fails
    # Razorpay SDK ignores order_id=undefined but errors on order_id=""
    rzp_order_id = txn.get("razorpay_order_id", "")
    return {
        "key_id": settings.razorpay_key_id,
        "order_id": rzp_order_id if rzp_order_id else None,
        "amount": txn["amount"],
        "currency": "INR",
        "product_name": txn["product_name"],
        "transaction_id": txn["id"],
        "customer": {
            "name": customer.get("name", "Gagan Singhal"),
            "email": customer.get("email", settings.demo_email),
            "contact": customer.get("phone", settings.demo_phone_number),
        },
        "scenario_key": scenario_key,
    }


from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class GatewayFailurePayload(BaseModel):
    scenario_key: str = "bank_decline"
    transaction_id: Optional[str] = None
    order_id: Optional[str] = None
    payment_id: Optional[str] = None
    error_code: Optional[str] = "GATEWAY_ERROR"
    error_description: Optional[str] = "Payment failed at bank"
    error_source: Optional[str] = "gateway"
    error_reason: Optional[str] = "payment_failed"


class GatewaySuccessPayload(BaseModel):
    transaction_id: Optional[str] = None
    order_id: Optional[str] = None
    payment_id: Optional[str] = None
    amount: Optional[int] = None


@router.post("/report-gateway-failure")
async def report_gateway_failure(payload: GatewayFailurePayload):
    """Called directly when Razorpay checkout popup triggers a payment.failed event."""
    scenario_key = payload.scenario_key
    txn_id = payload.transaction_id

    # Bug Fix #2: Fetch existing transaction by ID first, then fallback to order_id
    txn = None
    if txn_id:
        res = supabase.table("transactions").select("*").eq("id", txn_id).execute()
        if res.data:
            txn = res.data[0]

    if not txn and payload.order_id:
        res = supabase.table("transactions").select("*").eq("razorpay_order_id", payload.order_id).execute()
        if res.data:
            txn = res.data[0]
            print(f"🔍 Found transaction by order_id fallback: {txn['id']}")

    if not txn:
        txn = build_live_transaction(scenario_key)
        if txn_id:
            txn["id"] = txn_id

    # Bug Fix #1: ALWAYS use the scenario's hardcoded failure attributes
    # Razorpay sends the same generic error for ALL failure types, so we MUST
    # use the scenario config to ensure the agents see the correct failure type.
    scenario_info = SCENARIOS.get(scenario_key, {}).get("transaction", {})

    if scenario_key in SCENARIOS:
        # Known scenario — use hardcoded values, ignore Razorpay's generic errors
        txn.update({
            "status": "failed",
            "failure_reason": scenario_info.get("failure_reason", scenario_key),
            "error_code": scenario_info.get("error_code", "GATEWAY_ERROR"),
            "error_description": scenario_info.get("error_description", "Payment failed at bank"),
            "error_source": scenario_info.get("error_source", "gateway"),
            "razorpay_payment_id": payload.payment_id or "",
            "recovery_status": "pending",
            "is_live_demo": True,
        })
    else:
        # Unknown scenario — use Razorpay's actual error data
        failure_reason = "card_expired" if "expired" in (payload.error_description or "").lower() else "bank_decline"
        txn.update({
            "status": "failed",
            "failure_reason": failure_reason,
            "error_code": payload.error_code or "GATEWAY_ERROR",
            "error_description": payload.error_description or "Payment failed at bank",
            "error_source": payload.error_source or "gateway",
            "razorpay_payment_id": payload.payment_id or "",
            "recovery_status": "pending",
            "is_live_demo": True,
        })

    supabase.table("transactions").upsert(txn).execute()
    print(f"✅ Gateway failure recorded: txn={txn['id']}, scenario={scenario_key}, failure_reason={txn['failure_reason']}")

    # Overrides for scenarios like opted_out
    overrides = get_customer_override(scenario_key)
    if overrides:
        supabase.table("customers").update(overrides).eq("id", "cust_001").execute()

    customer = await get_customer("cust_001") or {}

    # Bug Fix #3: Use asyncio.create_task() for reliable fire-and-forget
    # BackgroundTasks can be cancelled if the HTTP connection drops before the task starts
    asyncio.create_task(_process_live(txn, customer, overrides))

    return {
        "status": "processing",
        "transaction_id": txn["id"],
        "failure_reason": txn["failure_reason"],
        "message": f"Gateway failure received! Scenario '{scenario_key}' → 6-agent swarm activated.",
    }


@router.post("/report-gateway-success")
async def report_gateway_success(payload: GatewaySuccessPayload):
    """Called when payment succeeds to mark recovered in DB and trigger Analyst learning."""
    txn_id = payload.transaction_id
    if txn_id:
        supabase.table("transactions").update({
            "recovery_status": "recovered",
            "status": "success",
            "razorpay_payment_id": payload.payment_id or "",
            "recovered_at": datetime.utcnow().isoformat(),
        }).eq("id", txn_id).execute()

        # Trigger Agent 6 (Analyst) to learn from the successful recovery, update RAG playbook, and log insights
        from agents.analyst import trigger_post_recovery_analysis
        asyncio.create_task(trigger_post_recovery_analysis(txn_id, payload.amount, payload.payment_id or ""))

    return {"status": "recovered", "transaction_id": txn_id}


@router.post("/trigger/{scenario_key}")
async def trigger_scenario(scenario_key: str):
    """Trigger a live demo scenario. Processes through the 6-agent swarm in the background."""
    if scenario_key not in SCENARIOS:
        return {"error": f"Unknown scenario: {scenario_key}"}

    # Build the live transaction
    txn = build_live_transaction(scenario_key)

    # Insert into Supabase
    supabase.table("transactions").upsert(txn).execute()

    # Apply customer overrides if any (e.g., opted_out for scenario 5)
    overrides = get_customer_override(scenario_key)
    if overrides:
        supabase.table("customers").update(overrides).eq("id", "cust_001").execute()

    # Get the demo customer
    customer = await get_customer("cust_001")

    # Bug Fix #3: Use asyncio.create_task() for reliable fire-and-forget
    asyncio.create_task(_process_live(txn, customer, overrides))

    return {
        "status": "processing",
        "transaction_id": txn["id"],
        "scenario": SCENARIOS[scenario_key]["description"],
        "message": "Watch the agent feed for live updates!",
    }


async def _process_live(txn: dict, customer: dict, overrides: dict):
    """Background task: process a live transaction through the swarm."""
    try:
        await process_transaction(txn, customer, is_live=True)
    except Exception as e:
        print(f"❌ Live scenario error: {e}")
    finally:
        # Revert customer overrides
        if overrides:
            revert = {k: False for k in overrides}
            supabase.table("customers").update(revert).eq("id", "cust_001").execute()


@router.post("/approve/{transaction_id}")
async def approve_human_review(transaction_id: str, background_tasks: BackgroundTasks):
    """Approve a transaction that was held for human review (amount gate)."""
    # Get the transaction
    result = supabase.table("transactions").select("*, customers(*)").eq("id", transaction_id).single().execute()
    txn = result.data

    if not txn:
        return {"error": "Transaction not found"}

    customer = txn.get("customers", {}) or {}

    # Update status to in_progress
    supabase.table("transactions").update({"recovery_status": "in_progress"}).eq("id", transaction_id).execute()

    # Process execution in background
    background_tasks.add_task(_process_approved_transaction, txn, customer)

    return {"status": "approved", "message": "Transaction approved! Recovery agent is now executing communication."}


@router.post("/delete-phone-records/{phone}")
async def delete_phone_records(phone: str):
    """Delete channel messages and clean up customer records for testing."""
    clean_phone = phone.replace("+", "").replace("-", "").replace(" ", "").strip()
    
    # 1. Find customer IDs matching this phone number
    cust_res = supabase.table("customers").select("id, name, phone").execute()
    matching_cust_ids = []
    for c in (cust_res.data or []):
        cust_phone = (c.get("phone") or "").replace("+", "").replace("-", "").replace(" ", "").strip()
        if clean_phone in cust_phone or cust_phone in clean_phone or c["id"] == "cust_001":
            matching_cust_ids.append(c["id"])
            
    deleted_messages = 0
    deleted_promises = 0
    
    for cid in matching_cust_ids:
        # Delete channel messages for this customer
        m_res = supabase.table("channel_messages").delete().eq("customer_id", cid).execute()
        deleted_messages += len(m_res.data or [])
        
        # Delete promise_to_pay for this customer
        p_res = supabase.table("promise_to_pay").delete().eq("customer_id", cid).execute()
        deleted_promises += len(p_res.data or [])

    # Also delete any channel messages containing the phone number or whatsapp in message_content
    raw_m = supabase.table("channel_messages").delete().ilike("message_content", f"%{clean_phone}%").execute()
    deleted_messages += len(raw_m.data or [])

    return {
        "status": "success",
        "phone": phone,
        "matched_customer_ids": matching_cust_ids,
        "deleted_channel_messages": deleted_messages,
        "deleted_promises": deleted_promises
    }


async def _process_approved_transaction(txn: dict, customer: dict):
    """Execute recovery for a human-approved high-value transaction."""
    try:
        from database import insert_recovery_action
        from agents.executor import executor_node
        from agents.analyst import analyst_node

        # Log human approval action
        await insert_recovery_action({
            "transaction_id": txn["id"],
            "agent": "compliance",
            "action": "human_approved",
            "details": {"approved_by": "merchant_admin", "reason": "Manual override for high-value transaction"},
            "result": "approved",
            "duration_ms": 10,
        })

        # Build approved state
        approved_state = {
            "transaction_id": txn["id"],
            "razorpay_order_id": txn.get("razorpay_order_id", ""),
            "amount": txn["amount"],
            "currency": txn.get("currency", "INR"),
            "customer_id": txn["customer_id"],
            "customer_name": customer.get("name", "Customer"),
            "customer_phone": customer.get("phone", ""),
            "customer_email": customer.get("email", ""),
            "product_name": txn.get("product_name", "Order"),
            "failure_reason": txn.get("failure_reason", "unknown"),
            "error_code": txn.get("error_code", "UNKNOWN"),
            "error_description": txn.get("error_description", ""),
            "error_source": txn.get("error_source", "unknown"),
            "bank": txn.get("bank", "unknown"),
            "method": txn.get("method", "netbanking"),
            "is_live_demo": txn.get("is_live_demo", True),
            "sentinel_output": {},
            "diagnosis": {"root_cause": txn.get("failure_reason", "invoice_overdue")},
            "strategy": {
                "channel": "email" if txn.get("failure_reason") == "invoice_overdue" else "whatsapp",
                "language": customer.get("preferred_language", "english"),
                "tone": "professional",
            },
            "compliance_result": {
                "verdict": "approved",
                "checks_passed": ["human_approved"],
                "checks_failed": [],
                "modifications": [],
            },
            "execution_result": {},
            "analysis": {},
            "debates": [],
            "audit_trail": [],
            "status": "in_progress",
            "attempt_count": 0,
            "customer_context": customer,
        }

        # Run executor & analyst
        exec_out = await executor_node(approved_state)
        approved_state.update(exec_out)
        await analyst_node(approved_state)

    except Exception as e:
        print(f"❌ Approved transaction execution error: {e}")
