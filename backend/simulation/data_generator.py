"""
RecoverAI — Synthetic Data Generator
Generates 50 customers + 200 transactions with realistic failure patterns.
"""

import random
import uuid
import json
from datetime import datetime, timedelta
from config import settings

# ── Customer Pools ──

FIRST_NAMES = ["Aarav", "Vivaan", "Aditya", "Vihaan", "Arjun", "Sai", "Reyansh", "Ayaan", "Krishna", "Ishaan",
               "Ananya", "Diya", "Priya", "Saanvi", "Myra", "Aadhya", "Ira", "Riya", "Kavya", "Anika",
               "Rohan", "Kabir", "Shaurya", "Atharv", "Advait", "Dhruv", "Rudra", "Arnav", "Kartik", "Sahil",
               "Sneha", "Neha", "Pooja", "Tanvi", "Meera", "Nisha", "Swati", "Ritika", "Shruti", "Divya",
               "Rahul", "Amit", "Vikram", "Kunal", "Manish", "Suresh", "Rajesh", "Deepak", "Nikhil", "Gaurav"]

LAST_NAMES = ["Sharma", "Verma", "Patel", "Singh", "Kumar", "Gupta", "Agarwal", "Joshi", "Reddy", "Nair",
              "Shah", "Mehta", "Desai", "Chauhan", "Yadav", "Mishra", "Iyer", "Rao", "Pillai", "Saxena"]

CITIES = ["Mumbai", "Delhi", "Bangalore", "Hyderabad", "Chennai", "Kolkata", "Pune", "Ahmedabad",
          "Jaipur", "Lucknow", "Noida", "Gurgaon", "Kochi", "Indore", "Bhopal"]

SEGMENTS = ["vip", "regular", "regular", "regular", "new", "new", "b2b", "subscription"]

PRODUCTS = [
    ("Silk Kurta Set", 429900), ("Premium Headphones", 249900), ("Running Shoes", 599900),
    ("Laptop Stand", 189900), ("Skincare Kit", 149900), ("Cotton Bedsheet Set", 339900),
    ("Wireless Earbuds", 199900), ("Coffee Machine", 899900), ("Yoga Mat Premium", 129900),
    ("Leather Wallet", 89900), ("Smart Watch", 449900), ("Perfume Set", 299900),
    ("Kitchen Mixer", 349900), ("Organic Tea Set", 79900), ("Fitness Tracker", 259900),
    ("Designer Sunglasses", 179900), ("Portable Speaker", 399900), ("Meditation Cushion", 119900),
    ("Stainless Steel Bottle", 59900), ("Bamboo Toothbrush Set", 39900),
]

B2B_PRODUCTS = [
    ("Monthly SaaS License - Enterprise", 4500000), ("Bulk Office Supplies", 2500000),
    ("IT Support Contract - Q1", 7500000), ("Marketing Service Package", 3500000),
]

BANKS = ["HDFC", "ICICI", "SBI", "Axis", "Kotak", "Yes Bank", "PNB", "BOB", "IndusInd", "IDFC First"]
METHODS = ["card", "card", "card", "upi", "upi", "upi", "netbanking", "wallet"]

FAILURE_TYPES = {
    "insufficient_funds": {"error_code": "BAD_REQUEST_ERROR", "error_desc": "Payment failed due to insufficient funds", "source": "customer"},
    "bank_decline": {"error_code": "GATEWAY_ERROR", "error_desc": "Bank declined the transaction", "source": "gateway"},
    "card_expired": {"error_code": "BAD_REQUEST_ERROR", "error_desc": "Card validity has expired", "source": "customer"},
    "network_timeout": {"error_code": "GATEWAY_ERROR", "error_desc": "Bank server timed out", "source": "gateway"},
    "auth_failed": {"error_code": "BAD_REQUEST_ERROR", "error_desc": "Authentication failed - incorrect OTP", "source": "customer"},
    "checkout_abandoned": {"error_code": "BAD_REQUEST_ERROR", "error_desc": "Customer dropped off at payment page", "source": "customer"},
    "mandate_expired": {"error_code": "BAD_REQUEST_ERROR", "error_desc": "Auto-debit mandate has expired", "source": "customer"},
    "auto_debit_failed": {"error_code": "GATEWAY_ERROR", "error_desc": "Auto-debit charge failed", "source": "gateway"},
    "invoice_overdue": {"error_code": "N/A", "error_desc": "Invoice payment overdue", "source": "customer"},
}


def generate_customers(count: int = 50) -> list:
    """Generate synthetic customer profiles."""
    customers = []

    # Customer #1 is YOU (the demo user)
    customers.append({
        "id": "cust_001",
        "name": settings.demo_customer_name,
        "email": settings.demo_email,
        "phone": settings.demo_phone_number,
        "city": "Delhi",
        "segment": "vip",
        "lifetime_value": 4200000,
        "preferred_payment": "upi",
        "preferred_language": "hinglish",
        "preferred_channel": "whatsapp",
        "on_dnd": False,
        "opted_out": False,
        "is_live_demo": True,
    })

    for i in range(2, count + 1):
        first = random.choice(FIRST_NAMES)
        last = random.choice(LAST_NAMES)
        city = random.choice(CITIES)
        segment = random.choice(SEGMENTS)
        on_dnd = random.random() < 0.15  # 15% on DND
        opted_out = random.random() < 0.05  # 5% opted out

        customers.append({
            "id": f"cust_{i:03d}",
            "name": f"{first} {last}",
            "email": f"{first.lower()}.{last.lower()}@gmail.com",
            "phone": f"+919{random.randint(100000000, 999999999)}",
            "city": city,
            "segment": segment,
            "lifetime_value": random.randint(50000, 5000000),
            "preferred_payment": random.choice(["upi", "card", "netbanking"]),
            "preferred_language": random.choice(["english", "hinglish", "hindi"]),
            "preferred_channel": random.choice(["whatsapp", "sms", "email"]),
            "on_dnd": on_dnd,
            "opted_out": opted_out,
            "is_live_demo": False,
        })

    return customers


def generate_transactions(customers: list, count: int = 200) -> list:
    """Generate synthetic transactions with realistic failure distributions."""
    transactions = []
    base_time = datetime.utcnow() - timedelta(days=7)

    # Reserve 10 txns for live demo (customer_001)
    live_count = 0

    for i in range(1, count + 1):
        txn_id = f"txn_{i:03d}"
        time_offset = timedelta(hours=random.randint(0, 168), minutes=random.randint(0, 59))
        created_at = (base_time + time_offset).isoformat()

        # Determine status
        r = random.random()
        if r < 0.40:
            status = "success"
            failure_reason = None
        elif r < 0.70:
            status = "failed"
            failure_reason = random.choice(["insufficient_funds", "bank_decline", "card_expired", "network_timeout", "auth_failed"])
        elif r < 0.85:
            status = "abandoned"
            failure_reason = "checkout_abandoned"
        elif r < 0.95:
            status = "failed"
            failure_reason = random.choice(["mandate_expired", "auto_debit_failed"])
        else:
            status = "overdue"
            failure_reason = "invoice_overdue"

        # Select customer (not customer_001 for batch)
        customer = random.choice(customers[1:])

        # Select product
        if customer["segment"] == "b2b":
            product_name, amount = random.choice(B2B_PRODUCTS)
        else:
            product_name, amount = random.choice(PRODUCTS)

        bank = random.choice(BANKS)
        method = random.choice(METHODS)

        txn = {
            "id": txn_id,
            "razorpay_order_id": f"order_{uuid.uuid4().hex[:12]}",
            "customer_id": customer["id"],
            "amount": amount,
            "product_name": product_name,
            "method": method,
            "bank": bank,
            "status": status,
            "failure_reason": failure_reason,
            "recovery_status": "pending" if status != "success" else None,
            "is_live_demo": False,
            "created_at": created_at,
        }

        if failure_reason and failure_reason in FAILURE_TYPES:
            ft = FAILURE_TYPES[failure_reason]
            txn["error_code"] = ft["error_code"]
            txn["error_description"] = ft["error_desc"]
            txn["error_source"] = ft["source"]

        transactions.append(txn)

    # Inject HDFC outage pattern: 12 failures in a 20-minute window
    outage_time = base_time + timedelta(days=3, hours=14)
    for j in range(12):
        idx = len(transactions) - 12 + j
        if idx < len(transactions):
            transactions[idx]["bank"] = "HDFC"
            transactions[idx]["failure_reason"] = "bank_decline"
            transactions[idx]["error_code"] = "GATEWAY_ERROR"
            transactions[idx]["error_description"] = "Bank server returned error code 05 - Do Not Honor"
            transactions[idx]["error_source"] = "gateway"
            transactions[idx]["status"] = "failed"
            transactions[idx]["recovery_status"] = "pending"
            transactions[idx]["created_at"] = (outage_time + timedelta(minutes=j * 2)).isoformat()
            transactions[idx]["is_outage_related"] = True

    return transactions
