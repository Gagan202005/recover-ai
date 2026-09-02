"""
RecoverAI — Batch Runner
Run ONCE before demo: generates data + processes transactions through agent swarm.
This trains the RAG playbook and populates the dashboard.
"""

import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from simulation.data_generator import generate_customers, generate_transactions
from database import supabase
from agents.swarm import process_transaction


async def seed_data():
    """Generate and insert customers + transactions into Supabase."""
    print("🔄 Generating 50 customers...")
    customers = generate_customers(50)

    print("🔄 Inserting customers into Supabase...")
    for c in customers:
        try:
            supabase.table("customers").upsert(c).execute()
        except Exception as e:
            print(f"  ⚠️  Customer {c['id']}: {e}")

    print("🔄 Generating 200 transactions...")
    transactions = generate_transactions(customers, 200)

    print("🔄 Inserting transactions into Supabase...")
    for t in transactions:
        try:
            supabase.table("transactions").upsert(t).execute()
        except Exception as e:
            print(f"  ⚠️  Transaction {t['id']}: {e}")

    # Seed A/B tests
    ab_tests = [
        {"experiment_name": "WhatsApp vs SMS for card_expired", "failure_type": "card_expired",
         "variant_a": "whatsapp", "variant_b": "sms"},
        {"experiment_name": "WhatsApp vs Email for checkout_abandoned", "failure_type": "checkout_abandoned",
         "variant_a": "whatsapp", "variant_b": "email"},
    ]
    for test in ab_tests:
        try:
            supabase.table("ab_tests").upsert(test, on_conflict="experiment_name").execute()
        except Exception:
            pass

    print(f"✅ Seeded {len(customers)} customers + {len(transactions)} transactions + {len(ab_tests)} A/B tests")
    return customers, transactions


async def run_batch():
    """Process all non-success transactions through the 6-agent swarm."""
    customers, transactions = await seed_data()

    # Build customer lookup
    customer_map = {c["id"]: c for c in customers}

    # Filter: only failed/abandoned/overdue (not success)
    to_process = [t for t in transactions if t["status"] != "success" and t.get("recovery_status") == "pending"]
    print(f"\n🤖 Processing {len(to_process)} transactions through 6-agent swarm...\n")

    recovered_count = 0
    exception_count = 0

    for i, txn in enumerate(to_process):
        customer = customer_map.get(txn["customer_id"], {})
        try:
            result = await process_transaction(txn, customer, is_live=False)
            status = result.get("status", "unknown")

            if status == "recovered":
                recovered_count += 1
                icon = "💰"
            elif status == "exception":
                exception_count += 1
                icon = "❌"
            else:
                icon = "🔄"

            print(f"  {icon} [{i+1}/{len(to_process)}] {txn['id']} | ₹{txn['amount']//100:,} | {txn.get('failure_reason','')} → {status}")

        except Exception as e:
            print(f"  ⚠️  [{i+1}/{len(to_process)}] {txn['id']} ERROR: {e}")

    print(f"\n{'='*60}")
    print(f"✅ BATCH COMPLETE")
    print(f"   Processed: {len(to_process)}")
    print(f"   Recovered: {recovered_count} 💰")
    print(f"   Exceptions: {exception_count} ❌")
    print(f"   In progress: {len(to_process) - recovered_count - exception_count} 🔄")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    asyncio.run(run_batch())
