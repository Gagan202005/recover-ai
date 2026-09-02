"""
RecoverAI — Agent 1: SENTINEL
Detection & Triage — calculates urgency, generates fingerprint, deduplicates.
"""

import hashlib
import time
from datetime import datetime
from agents.state import RecoveryState
from database import get_customer, insert_recovery_action


FAILURE_RECOVERABILITY = {
    "network_timeout": 0.9, "bank_decline": 0.7, "bank_outage": 0.8,
    "insufficient_funds": 0.5, "card_expired": 0.4, "auth_failed": 0.3,
    "checkout_abandoned": 0.3, "mandate_expired": 0.5, "auto_debit_failed": 0.6,
    "invoice_overdue": 0.6,
}


async def sentinel_node(state: RecoveryState) -> dict:
    """Sentinel agent: detect, triage, and calculate urgency."""
    start_time = time.time()

    # Load customer context
    db_customer = await get_customer(state["customer_id"])
    customer = {**(db_customer or {}), **state.get("customer_context", {})}
    ltv = customer.get("lifetime_value", 0)
    segment = customer.get("segment", "regular")

    # Normalize amount (0-1 scale, capped at ₹50,000)
    amount_norm = min(state["amount"] / 5000000, 1.0)

    # Normalize LTV
    ltv_norm = min(ltv / 10000000, 1.0)

    # Recency: live demos get max recency
    recency_norm = 1.0 if state.get("is_live_demo") else 0.5

    # Recoverability based on failure type
    recoverability = FAILURE_RECOVERABILITY.get(state.get("failure_reason", ""), 0.5)

    # Urgency score
    urgency = (amount_norm * 0.4) + (ltv_norm * 0.3) + (recency_norm * 0.2) + (recoverability * 0.1)

    # Failure fingerprint (for correlation)
    fp_string = f"{state.get('bank', 'unknown')}|{state.get('error_code', 'unknown')}|{datetime.utcnow().strftime('%Y%m%d%H')}"
    fingerprint = hashlib.md5(fp_string.encode()).hexdigest()[:12]

    # Priority
    if urgency > 0.7:
        priority = "critical"
    elif urgency > 0.4:
        priority = "high"
    else:
        priority = "medium"

    sentinel_output = {
        "urgency_score": round(urgency, 3),
        "fingerprint": fingerprint,
        "failure_type": state.get("failure_reason", "unknown"),
        "priority": priority,
        "segment": segment,
        "recoverability": recoverability,
    }

    duration_ms = int((time.time() - start_time) * 1000)

    # Log to audit trail
    await insert_recovery_action({
        "transaction_id": state["transaction_id"],
        "agent": "sentinel",
        "action": "detected",
        "details": sentinel_output,
        "result": "success",
        "duration_ms": duration_ms,
    })

    return {
        "sentinel_output": sentinel_output,
        "customer_context": {
            "segment": segment,
            "preferred_language": customer.get("preferred_language", "english"),
            "preferred_channel": customer.get("preferred_channel", "whatsapp"),
            "on_dnd": customer.get("on_dnd", False),
            "opted_out": customer.get("opted_out", False),
            "lifetime_value": ltv,
            "city": customer.get("city", ""),
        },
        "status": "processing",
        "audit_trail": state.get("audit_trail", []) + [{"agent": "sentinel", "action": "detected", "ts": datetime.utcnow().isoformat()}],
        "debates": state.get("debates", []),
    }
