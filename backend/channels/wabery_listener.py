"""
RecoverAI — Channel: Wabery Live Two-Way Polling Listener
Powered by Gemini Conversational Intelligence.
Continuously polls Wabery, extracts intents, updates Supabase, and dispatches context-aware AI replies.

This module is started automatically by FastAPI lifespan (main.py) — no separate process needed.
"""

import asyncio
import os
import sys
import requests
from datetime import datetime
from collections import OrderedDict

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import settings
from database import supabase, get_customer
from agents.conversational_agent import handle_customer_reply
from channels.wabery_client import send_whatsapp as send_wabery_msg

WABERY_API_KEY = os.getenv("WABERY_API_KEY", settings.wabery_api_key)
WABERY_CONVERSATION_ID = os.getenv("WABERY_CONVERSATION_ID", settings.wabery_conversation_id)

# ── Shared Dedup Set ──
# Used by both polling listener AND webhook handler to prevent duplicate replies.
# Max 2000 entries — evicts oldest when full.
MAX_DEDUP_SIZE = 2000


class MessageDedup:
    """Thread-safe deduplication tracker for processed WhatsApp message IDs."""
    def __init__(self, max_size: int = MAX_DEDUP_SIZE):
        self._seen = OrderedDict()
        self._max_size = max_size

    def is_seen(self, msg_id: str) -> bool:
        return msg_id in self._seen

    def mark_seen(self, msg_id: str):
        if not msg_id or msg_id in self._seen:
            return
        if len(self._seen) >= self._max_size:
            self._seen.popitem(last=False)  # Evict oldest
        self._seen[msg_id] = True

    def __contains__(self, msg_id: str) -> bool:
        return self.is_seen(msg_id)


# Singleton shared across polling listener + webhook handler
message_dedup = MessageDedup()


async def process_inbound_message(
    msg_id: str,
    content: str,
    phone: str = "+918077344252",
    conv_id: str = None,
    chan_id: str = None,
    contact_name: str = "Gagan Singhal"
):
    """Process a new customer message with Gemini AI and dispatch real WhatsApp reply."""
    if not content:
        return

    # Dedup check — skip if already processed (by polling or webhook)
    if message_dedup.is_seen(msg_id):
        return
    message_dedup.mark_seen(msg_id)

    print(f"\n📥 [Wabery Live Listener] New Customer Message: '{content}' (ID: {msg_id}, From: {phone})")

    try:
        # Fetch customer (safe query with fallback)
        customer = {
            "id": "cust_001",
            "name": contact_name or "Gagan Singhal",
            "preferred_language": "hinglish",
            "phone": phone
        }
        try:
            phone_clean = phone.replace("+91", "").replace("+", "").strip()
            phone_variants = [phone, f"+91{phone_clean}", phone_clean]
            customers = supabase.table("customers").select("*").in_("phone", phone_variants).execute()
            if customers.data:
                customer = customers.data[0]
            else:
                # Try fallback by name or cust_001
                c_fallback = supabase.table("customers").select("*").eq("id", "cust_001").execute()
                if c_fallback.data:
                    customer = c_fallback.data[0]
                    customer["phone"] = phone
        except Exception as db_err:
            print(f"⚠️ [Wabery Live Listener] Customer DB lookup error: {db_err}. Using default profile.")

        # Run Gemini AI Conversational Recovery Agent
        result = await handle_customer_reply(customer, content, channel="whatsapp", message_id=msg_id)
        reply_text = result.get("reply", "")
        intent = result.get("intent", "other")
        promise_date = result.get("promise_date")

        if reply_text:
            # Send Reply via Wabery to WhatsApp!
            print(f"🚀 [Wabery Live Listener] Intent: {intent} | Promise Date: {promise_date} | Reply: '{reply_text[:80]}...'")
            send_result = send_wabery_msg(phone, reply_text, conv_id=conv_id, chan_id=chan_id)
            print(f"📤 [Wabery Live Listener] Send result: {send_result.get('status', 'unknown')}")
        else:
            print(f"⚠️ [Wabery Live Listener] Empty reply from conversational agent for message: '{content}'")

    except Exception as e:
        print(f"❌ [Wabery Live Listener] Error processing message '{content[:50]}': {e}")
        import traceback
        traceback.print_exc()


async def start_polling_loop():
    """Continuously poll Wabery for new inbound customer messages.
    Pre-populates seen message IDs from Supabase and current Wabery conversations on boot."""
    await asyncio.sleep(2)  # Allow FastAPI to finish startup first
    headers = {"Authorization": f"Bearer {WABERY_API_KEY}"}

    if not WABERY_API_KEY:
        print("⚠️ [Wabery Live Listener] WABERY_API_KEY not set. Polling disabled.")
        return

    # Pre-populate dedup tracker from database to never re-process historical messages on reload
    try:
        past_msgs = supabase.table("channel_messages").select("external_id").not_.is_("external_id", "null").limit(500).execute()
        for row in (past_msgs.data or []):
            ext_id = row.get("external_id")
            if ext_id:
                message_dedup.mark_seen(ext_id)
        print(f"🔒 [Wabery Live Listener] Loaded {len(past_msgs.data or [])} historical message IDs into dedup cache.")
    except Exception as e:
        print(f"⚠️ [Wabery Live Listener] Dedup preload warning: {e}")

    # Seed existing messages currently in Wabery conversations (with order=desc) so only NEW messages trigger replies
    active_conversations = []
    try:
        r_conv = await asyncio.to_thread(requests.get, "https://api.wabery.com/v1/conversations", headers=headers, timeout=5)
        if r_conv.status_code == 200:
            active_conversations = r_conv.json().get("data", [])
            for c in active_conversations:
                cid = c.get("id")
                if not cid:
                    continue
                # Fetch newest 50 messages to mark as seen on initial boot
                msg_r = await asyncio.to_thread(
                    requests.get,
                    f"https://api.wabery.com/v1/conversations/{cid}/messages",
                    headers=headers,
                    params={"order": "desc", "limit": 50},
                    timeout=5
                )
                if msg_r.status_code == 200:
                    existing = msg_r.json().get("data", [])
                    for m in existing:
                        m_id = m.get("id")
                        if m_id:
                            message_dedup.mark_seen(m_id)
            print(f"🔒 [Wabery Live Listener] Seeded existing conversation messages into dedup cache across {len(active_conversations)} conversation(s).")
    except Exception as e:
        print(f"⚠️ [Wabery Live Listener] Wabery seeding error: {e}")

    print("🟢 [Wabery Live Listener] Started continuous polling loop (every 3s)...")
    if WABERY_CONVERSATION_ID:
        print(f"   📡 Primary Conversation ID: {WABERY_CONVERSATION_ID}")

    poll_cycle = 0

    while True:
        try:
            poll_cycle += 1
            # Periodically (every 10 cycles = 30s) refresh the active conversations list
            if poll_cycle % 10 == 1 or not active_conversations:
                try:
                    r_conv = await asyncio.to_thread(requests.get, "https://api.wabery.com/v1/conversations", headers=headers, timeout=5)
                    if r_conv.status_code == 200:
                        active_conversations = r_conv.json().get("data", [])
                except Exception:
                    pass

            # If no conversations found via API, fallback to configured WABERY_CONVERSATION_ID
            conv_targets = active_conversations if active_conversations else [{"id": WABERY_CONVERSATION_ID, "phone": "+918077344252"}]

            for c in conv_targets:
                conv_id = c.get("id") or WABERY_CONVERSATION_ID
                if not conv_id:
                    continue

                phone = c.get("phone") or "+918077344252"
                contact_name = c.get("name") or "Gagan Singhal"
                chan_id = c.get("last_channel_id") or c.get("channel_id") or settings.wabery_channel_id

                url = f"https://api.wabery.com/v1/conversations/{conv_id}/messages"
                # CRITICAL: Always pass order=desc to retrieve the NEWEST messages first!
                r = await asyncio.to_thread(requests.get, url, headers=headers, params={"order": "desc", "limit": 20}, timeout=5)
                
                if r.status_code == 200:
                    msgs = r.json().get("data", [])
                    # msgs is ordered newest-to-oldest. Reverse it so we process oldest-to-newest in this fresh slice.
                    for m in reversed(msgs):
                        if m.get("direction") == "inbound":
                            msg_id = m.get("id")
                            content = (m.get("content") or "").strip()
                            # Ignore initial sandbox handshake
                            if content and not content.startswith("wab-") and content != "Hello":
                                if not message_dedup.is_seen(msg_id):
                                    await process_inbound_message(
                                        msg_id=msg_id,
                                        content=content,
                                        phone=phone,
                                        conv_id=conv_id,
                                        chan_id=chan_id,
                                        contact_name=contact_name
                                    )
                elif r.status_code == 401:
                    print("❌ [Wabery Live Listener] Auth failed (401). Check WABERY_API_KEY.")
                    await asyncio.sleep(60)  # Back off on auth failure
                    break

        except requests.exceptions.Timeout:
            pass  # Timeout is fine, just retry
        except requests.exceptions.ConnectionError:
            print("⚠️ [Wabery Live Listener] Connection error. Retrying in 10s...")
            await asyncio.sleep(10)
        except Exception as e:
            print(f"⚠️ [Wabery Live Listener] Polling Error: {e}")

        await asyncio.sleep(3)  # Check every 3 seconds


if __name__ == "__main__":
    asyncio.run(start_polling_loop())

