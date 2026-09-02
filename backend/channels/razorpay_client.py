"""
RecoverAI — Channel: Razorpay Client
Wrapper around Razorpay Python SDK (test mode).
"""

import time
import razorpay
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import settings


def get_razorpay_client() -> razorpay.Client:
    client = razorpay.Client(auth=(settings.razorpay_key_id, settings.razorpay_key_secret))
    client.set_app_details({"title": "RecoverAI", "version": "1.0.0"})
    return client


rzp_client = get_razorpay_client()


def create_order(amount: int, currency: str = "INR", receipt: str = "") -> dict:
    return rzp_client.order.create({"amount": amount, "currency": currency, "receipt": receipt})


def create_payment_link(amount: int, customer_name: str, customer_email: str,
                         customer_phone: str, description: str, currency: str = "INR",
                         expire_hours: int = 24, callback_url: str = "") -> dict:
    data = {
        "amount": amount, "currency": currency, "description": description,
        "customer": {"name": customer_name, "email": customer_email, "contact": customer_phone},
        "notify": {"sms": False, "email": False}, "reminder_enable": False,
        "expire_by": int(time.time()) + (expire_hours * 3600),
    }
    if callback_url:
        data["callback_url"] = callback_url
    return rzp_client.payment_link.create(data)


def fetch_payment(payment_id: str) -> dict:
    return rzp_client.payment.fetch(payment_id)


def fetch_order_payments(order_id: str) -> list:
    return rzp_client.order.payments(order_id)


def create_subscription(plan_id: str, total_count: int = 12) -> dict:
    return rzp_client.subscription.create({"plan_id": plan_id, "total_count": total_count, "customer_notify": 0})


def create_invoice(amount: int, customer_name: str, customer_email: str, description: str) -> dict:
    return rzp_client.invoice.create({
        "type": "link", "amount": amount, "currency": "INR",
        "description": description, "customer": {"name": customer_name, "email": customer_email},
    })


def fetch_recent_failures(count: int = 30) -> list:
    """Fetch recent failed payments directly from Razorpay API."""
    try:
        res = rzp_client.payment.all({"count": count})
        items = res.get("items", []) if isinstance(res, dict) else res
        failed = [p for p in items if p.get("status") == "failed"]
        return failed
    except Exception as e:
        print(f"⚠️ Error fetching failed payments from Razorpay: {e}")
        return []


def verify_webhook_signature(body: str, signature: str) -> bool:
    try:
        rzp_client.utility.verify_webhook_signature(body, signature, settings.razorpay_webhook_secret)
        return True
    except Exception:
        return False
