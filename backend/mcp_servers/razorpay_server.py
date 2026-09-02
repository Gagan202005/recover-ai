"""
RecoverAI — MCP Server: Razorpay
7 tools for payment operations exposed via Model Context Protocol.
"""

import time
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from mcp.server.fastmcp import FastMCP
from channels.razorpay_client import (
    create_order, create_payment_link, fetch_payment,
    fetch_order_payments, create_subscription, create_invoice, rzp_client,
)

mcp = FastMCP("razorpay-recovery")


@mcp.tool()
def tool_create_payment_link(
    amount: int,
    currency: str,
    customer_name: str,
    customer_email: str,
    customer_phone: str,
    description: str,
    expire_hours: int = 24,
) -> dict:
    """Create a Razorpay payment link for recovery.
    Amount is in paise (e.g., 429900 = ₹4,299).
    Returns a real clickable short URL in test mode."""
    result = create_payment_link(
        amount=amount, customer_name=customer_name,
        customer_email=customer_email, customer_phone=customer_phone,
        description=description, currency=currency, expire_hours=expire_hours,
    )
    return {"link_id": result.get("id"), "short_url": result.get("short_url"), "status": "created"}


@mcp.tool()
def tool_create_order(amount: int, currency: str = "INR", receipt: str = "") -> dict:
    """Create a Razorpay order for a transaction."""
    result = create_order(amount=amount, currency=currency, receipt=receipt)
    return {"order_id": result.get("id"), "amount": result.get("amount"), "status": result.get("status")}


@mcp.tool()
def tool_fetch_payment_details(payment_id: str) -> dict:
    """Fetch details of a Razorpay payment by ID."""
    return fetch_payment(payment_id)


@mcp.tool()
def tool_fetch_order_payments(order_id: str) -> dict:
    """Fetch all payment attempts for a Razorpay order."""
    result = fetch_order_payments(order_id)
    return {"order_id": order_id, "payments": result.get("items", [])}


@mcp.tool()
def tool_create_subscription(plan_id: str, total_count: int = 12) -> dict:
    """Create a new subscription for mandate recovery."""
    result = create_subscription(plan_id=plan_id, total_count=total_count)
    return {"subscription_id": result.get("id"), "status": result.get("status")}


@mcp.tool()
def tool_create_invoice(
    amount: int, customer_name: str, customer_email: str, description: str,
) -> dict:
    """Create a Razorpay invoice for B2B recovery."""
    result = create_invoice(
        amount=amount, customer_name=customer_name,
        customer_email=customer_email, description=description,
    )
    return {"invoice_id": result.get("id"), "short_url": result.get("short_url"), "status": result.get("status")}


@mcp.tool()
def tool_list_failed_payments(from_timestamp: int, to_timestamp: int) -> dict:
    """List all failed payments in a date range (Unix timestamps)."""
    payments = rzp_client.payment.all({"from": from_timestamp, "to": to_timestamp, "count": 100})
    failed = [p for p in payments.get("items", []) if p.get("status") == "failed"]
    return {"count": len(failed), "payments": failed}


if __name__ == "__main__":
    mcp.run()
