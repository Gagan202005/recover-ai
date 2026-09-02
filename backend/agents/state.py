"""
RecoverAI — Agent State
Shared state schema for the LangGraph agent swarm.
"""

from typing import TypedDict, Literal, Optional


class RecoveryState(TypedDict, total=False):
    """Shared state passed between all 6 agents in the LangGraph swarm."""

    # ── Input (set by caller) ──
    transaction_id: str
    razorpay_order_id: str
    amount: int                         # in paise
    currency: str
    customer_id: str
    customer_name: str
    customer_phone: str
    customer_email: str
    product_name: str
    failure_reason: str
    error_code: str
    error_description: str
    error_source: str
    bank: str
    method: str
    is_live_demo: bool

    # ── Agent Outputs ──
    sentinel_output: dict
    diagnosis: dict
    strategy: dict
    compliance_result: dict
    execution_result: dict
    analysis: dict

    # ── Tracking ──
    debates: list
    audit_trail: list
    status: str
    attempt_count: int

    # ── Customer context ──
    customer_context: dict
