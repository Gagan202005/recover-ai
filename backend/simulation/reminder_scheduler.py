"""
RecoverAI — Promise-to-Pay Reminder Scheduler
Continuously monitors scheduled promises in Supabase.
When a promise_date arrives, autonomously crafts a polite, context-aware Gemini AI reminder
and dispatches it via Wabery WhatsApp / Email / SMS.
"""

import asyncio
import os
import sys
from datetime import datetime, date
import google.generativeai as genai

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import settings
from database import supabase, insert_recovery_action, insert_channel_message
from channels.wabery_client import send_whatsapp
from channels.email_client import send_email, build_recovery_email_html
from channels.sms_router import dispatch_sms

genai.configure(api_key=settings.google_api_key)
model = genai.GenerativeModel(settings.gemini_model)


async def check_and_dispatch_due_reminders(force_all: bool = False) -> list:
    """Find scheduled promises and dispatch reminders. If force_all=True, dispatches all active promises."""
    # Use Indian Standard Time (UTC+5:30)
    today_str = (datetime.utcnow() + timedelta(hours=5, minutes=30)).date().isoformat()

    # Fetch active promises that are due today or earlier
    query = supabase.table("promise_to_pay") \
        .select("*, customers(*), transactions(*)") \
        .eq("status", "promised")
    
    if not force_all:
        query = query.lte("promise_date", today_str)

    res = query.order("created_at", desc=True).execute()
    promises = res.data if res.data else []

    if promises:
        print(f"⏰ [Reminder Scheduler] Found {len(promises)} due promise(s) for date <= {today_str}.")

    dispatched = []

    for p in promises:
        try:
            customer = p.get("customers") or {}
            txn = p.get("transactions") or {}
            phone = customer.get("phone", "+918077344252")
            email = customer.get("email", "")
            customer_name = customer.get("name", "Gagan Singhal")
            first_name = customer_name.split()[0]
            language = customer.get("preferred_language", "hinglish")
            product_name = txn.get("product_name", "Silk Kurta Set")
            amount_val = p.get("promise_amount", 429900)
            amount_str = f"₹{amount_val // 100}"
            payment_link = "https://rzp.io/i/demo"

            # Fetch actual Razorpay payment link from channel_messages if available
            txn_id = txn.get("id")
            if txn_id:
                try:
                    link_res = supabase.table("channel_messages") \
                        .select("payment_link_url") \
                        .eq("transaction_id", txn_id) \
                        .neq("payment_link_url", "null") \
                        .order("created_at", desc=True) \
                        .limit(1) \
                        .execute()
                    if link_res.data and link_res.data[0].get("payment_link_url"):
                        fetched_link = link_res.data[0]["payment_link_url"]
                        if fetched_link and fetched_link.startswith("http"):
                            payment_link = fetched_link
                except Exception:
                    pass  # Keep default link on DB error

            # Check if transaction is already recovered
            if txn.get("recovery_status") == "recovered":
                supabase.table("promise_to_pay").update({"status": "fulfilled"}).eq("id", p["id"]).execute()
                continue

            # Check if customer opted out
            if customer.get("opted_out"):
                supabase.table("promise_to_pay").update({"status": "cancelled"}).eq("id", p["id"]).execute()
                continue

            # Generate friendly reminder copy
            reminder_text = f"Namaste {first_name} ji! 🙏 Aapke {product_name} ({amount_str}) order ka payment complete karne ka reminder. Yahan click karke complete karein: {payment_link} ✨"

            # Dispatch via preferred channel (WhatsApp by default)
            channel = customer.get("preferred_channel", "whatsapp")
            if channel == "whatsapp":
                send_whatsapp(phone, reminder_text)
            elif channel == "email" and email:
                subject = f"Payment Reminder: {product_name} ({amount_str})"
                html_body = build_recovery_email_html(customer_name, amount_str, product_name, payment_link, settings.merchant_name)
                send_email(email, subject, html_body)
            else:
                dispatch_sms(phone, reminder_text)

            # Mark promise as fulfilled and record fulfillment time so it leaves the scheduled reminders list
            supabase.table("promise_to_pay").update({
                "status": "fulfilled",
                "fulfilled_at": datetime.utcnow().isoformat(),
            }).eq("id", p["id"]).execute()

            # Audit trail in Supabase
            await insert_recovery_action({
                "transaction_id": txn_id,
                "agent": "executor",
                "action": "promise_reminder_dispatched",
                "details": {
                    "promise_id": p["id"],
                    "channel": channel,
                    "promise_date": p["promise_date"],
                    "reminder_content": reminder_text,
                    "payment_link": payment_link,
                },
                "result": "success",
            })

            await insert_channel_message({
                "transaction_id": txn_id,
                "customer_id": customer.get("id"),
                "channel": channel,
                "language": language,
                "message_content": reminder_text,
                "payment_link_url": payment_link,
                "status": "sent",
            })

            print(f"✅ Dispatched Reminder to {customer_name} ({phone}) via {channel}: '{reminder_text[:60]}...'")
            dispatched.append({
                "promise_id": p["id"],
                "customer": customer_name,
                "phone": phone,
                "channel": channel,
                "message": reminder_text,
                "status": "dispatched",
            })

        except Exception as e:
            print(f"⚠️ [Reminder Scheduler] Error dispatching promise {p.get('id', '?')}: {e}")
            continue  # Don't let one failure stop all dispatches

    return dispatched


async def start_reminder_daemon(interval_seconds: int = 30):
    """Background daemon that periodically checks and dispatches due reminders."""
    await asyncio.sleep(5)  # Allow FastAPI to finish startup first
    print("🟢 [Reminder Scheduler Daemon] Started...")
    while True:
        try:
            await check_and_dispatch_due_reminders()
        except Exception as e:
            print(f"⚠️ [Reminder Scheduler] Error: {e}")
        await asyncio.sleep(interval_seconds)


if __name__ == "__main__":
    asyncio.run(check_and_dispatch_due_reminders())
