"""
RecoverAI — Live Demo Scenarios
5 scenarios triggered by dashboard buttons during the judge demo.
"""

import uuid
from datetime import datetime
from config import settings


SCENARIOS = {
    "card_expired": {
        "description": "💳 Card Expired — WhatsApp recovery with real payment link",
        "transaction": {
            "amount": 429900,
            "product_name": "Silk Kurta Set",
            "method": "card",
            "bank": "HDFC",
            "status": "failed",
            "failure_reason": "card_expired",
            "error_code": "BAD_REQUEST_ERROR",
            "error_description": "Card validity has expired",
            "error_source": "customer",
        },
    },
    "invoice_overdue": {
        "description": "📄 B2B Invoice Overdue — AI Voice Reminder call + Email payment link",
        "transaction": {
            "amount": 4500000,
            "product_name": "IT Support Contract - Q1",
            "method": "netbanking",
            "bank": "ICICI",
            "status": "overdue",
            "failure_reason": "invoice_overdue",
            "error_code": "N/A",
            "error_description": "Invoice payment overdue by 7 days",
            "error_source": "customer",
        },
    },
    "checkout_abandoned": {
        "description": "🛒 Checkout Abandoned — Email recovery first with cart summary + LLM multi-channel follow-up",
        "transaction": {
            "amount": 899900,
            "product_name": "Coffee Machine",
            "method": "upi",
            "bank": "SBI",
            "status": "abandoned",
            "failure_reason": "checkout_abandoned",
            "error_code": "BAD_REQUEST_ERROR",
            "error_description": "Customer dropped off at payment page",
            "error_source": "customer",
        },
    },
    "opted_out": {
        "description": "❌ Opted-Out Customer (DND) — Compliance blocks ALL channels",
        "transaction": {
            "amount": 299900,
            "product_name": "Perfume Set",
            "method": "card",
            "bank": "Axis",
            "status": "failed",
            "failure_reason": "card_expired",
            "error_code": "BAD_REQUEST_ERROR",
            "error_description": "Card validity has expired",
            "error_source": "customer",
        },
        "customer_override": {"opted_out": True},
    },
    "bank_decline": {
        "description": "🏦 Bank Outage / Decline — Outage Radar + 2h auto-retry with payment link",
        "transaction": {
            "amount": 249900,
            "product_name": "Premium Headphones",
            "method": "card",
            "bank": "HDFC",
            "status": "failed",
            "failure_reason": "bank_decline",
            "error_code": "GATEWAY_ERROR",
            "error_description": "Bank server returned error code 05 - Do Not Honor",
            "error_source": "gateway",
        },
    },
}


def build_live_transaction(scenario_key: str) -> dict:
    """Build a transaction dict for a live demo scenario."""
    scenario = SCENARIOS[scenario_key]
    txn_template = scenario["transaction"]

    txn_id = f"live_{scenario_key}_{uuid.uuid4().hex[:6]}"

    return {
        "id": txn_id,
        "razorpay_order_id": f"order_live_{uuid.uuid4().hex[:8]}",
        "customer_id": "cust_001",  # Always the demo user
        **txn_template,
        "recovery_status": "pending",
        "is_live_demo": True,
        "created_at": datetime.utcnow().isoformat(),
    }


def get_customer_override(scenario_key: str) -> dict:
    """Get customer field overrides for a scenario (e.g., opted_out for scenario 5)."""
    scenario = SCENARIOS.get(scenario_key, {})
    return scenario.get("customer_override", {})
