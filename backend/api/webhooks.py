"""
RecoverAI — API: Webhooks
Razorpay payment events + Twilio/Wabery WhatsApp incoming messages.
"""

import json
from fastapi import APIRouter, Request, Response
from database import supabase, insert_channel_message
from channels.twilio_client import create_whatsapp_reply
from config import settings
from datetime import datetime

router = APIRouter(prefix="/api/webhooks", tags=["webhooks"])


@router.post("/razorpay")
async def razorpay_webhook(request: Request):
    """Handle Razorpay payment events (payment.captured, payment.failed, etc.)."""
    body = await request.body()
    signature = request.headers.get("X-Razorpay-Signature", "")

    try:
        payload = json.loads(body)
        event = payload.get("event", "")
        entity = payload.get("payload", {}).get("payment", {}).get("entity", {})

        if event == "payment.captured":
            order_id = entity.get("order_id", "")
            # Find the transaction and mark as recovered
            txns = supabase.table("transactions").select("*").eq("razorpay_order_id", order_id).execute()
            if txns.data:
                txn = txns.data[0]
                rec_amount = entity.get("amount", txn["amount"])
                payment_id = entity.get("id", "")
                supabase.table("transactions").update({
                    "recovery_status": "recovered",
                    "status": "success",
                    "recovery_amount": rec_amount,
                    "razorpay_payment_id": payment_id,
                    "recovered_at": datetime.utcnow().isoformat(),
                }).eq("id", txn["id"]).execute()

                # Trigger Agent 6 (Analyst)
                import asyncio
                from agents.analyst import trigger_post_recovery_analysis
                asyncio.create_task(trigger_post_recovery_analysis(txn["id"], rec_amount, payment_id))

        elif event == "payment.failed":
            order_id = entity.get("order_id", "")
            error_code = entity.get("error_code", "GATEWAY_ERROR")
            error_desc = entity.get("error_description", "Payment failed at bank")
            error_source = entity.get("error_source", "gateway")
            bank = entity.get("bank", "HDFC")
            method = entity.get("method", "card")
            amount = entity.get("amount", 299900)

            # Determine failure reason
            desc_low = (error_desc or "").lower()
            if "expired" in desc_low:
                failure_reason = "card_expired"
            elif "insufficient" in desc_low or "balance" in desc_low:
                failure_reason = "insufficient_funds"
            elif "timeout" in desc_low:
                failure_reason = "network_timeout"
            else:
                failure_reason = "bank_decline"

            # Check if transaction already exists by order_id
            txns = supabase.table("transactions").select("*").eq("razorpay_order_id", order_id).execute() if order_id else None
            if txns and txns.data:
                txn = txns.data[0]
                supabase.table("transactions").update({
                    "status": "failed",
                    "failure_reason": failure_reason,
                    "error_code": error_code,
                    "error_description": error_desc,
                    "error_source": error_source,
                }).eq("id", txn["id"]).execute()
            else:
                import uuid
                txn_id = f"live_rzp_{uuid.uuid4().hex[:6]}"
                txn = {
                    "id": txn_id,
                    "razorpay_order_id": order_id or f"order_{uuid.uuid4().hex[:8]}",
                    "customer_id": "cust_001",
                    "amount": amount,
                    "product_name": entity.get("description", "Online Order"),
                    "method": method,
                    "bank": bank,
                    "status": "failed",
                    "failure_reason": failure_reason,
                    "error_code": error_code,
                    "error_description": error_desc,
                    "error_source": error_source,
                    "recovery_status": "pending",
                    "is_live_demo": True,
                    "created_at": datetime.utcnow().isoformat(),
                }
                supabase.table("transactions").upsert(txn).execute()

            # Trigger 6-agent swarm
            from agents.swarm import process_transaction
            from database import get_customer
            customer = await get_customer("cust_001")
            import asyncio
            asyncio.create_task(process_transaction(txn, customer, is_live=True))

    except Exception as e:
        print(f"⚠️ Razorpay webhook error: {e}")

    return {"status": "ok"}


@router.post("/twilio/whatsapp")
async def twilio_whatsapp_webhook(request: Request):
    """Handle incoming WhatsApp messages from customers (two-way WhatsApp via Twilio)."""
    form_data = await request.form()
    from_number = form_data.get("From", "").replace("whatsapp:", "")
    body = form_data.get("Body", "").strip()
    message_sid = form_data.get("MessageSid", "")

    if not body:
        return Response(content=create_whatsapp_reply("Sorry, I didn't understand that."), media_type="application/xml")

    # Find customer
    customers = supabase.table("customers").select("*").eq("phone", from_number).execute()
    if not customers.data:
        return Response(content=create_whatsapp_reply("Thanks for your message! Please contact our support team."), media_type="application/xml")

    customer = customers.data[0]

    # Use the unified Gemini-powered Conversational Agent (same quality as Wabery path)
    from agents.conversational_agent import handle_customer_reply
    result = await handle_customer_reply(customer, body, channel="whatsapp", message_id=message_sid)
    reply = result.get("reply", "Thank you for your message! Our team will get back to you soon. 🙏")

    return Response(content=create_whatsapp_reply(reply), media_type="application/xml")



@router.post("/wabery")
@router.get("/wabery")
async def wabery_webhook(request: Request):
    """Handle incoming WhatsApp messages & test pings from Wabery.
    Shares dedup set with the polling listener to prevent double-replies."""
    try:
        body = await request.body()
        if not body:
            return {"status": "ok", "message": "Wabery webhook alive"}

        payload = json.loads(body)
        event_type = payload.get("type", "")

        # Handle incoming user message
        msg_obj = payload.get("message", {}) if isinstance(payload.get("message"), dict) else payload
        text = (
            payload.get("content", "")
            or msg_obj.get("content", "")
            or payload.get("text", "")
            or msg_obj.get("text", "")
        )
        contact = payload.get("contact", {}) if isinstance(payload.get("contact"), dict) else {}
        phone = contact.get("phone", "") or payload.get("phone", "") or "+918077344252"
        msg_id = (
            payload.get("id", "")
            or msg_obj.get("id", "")
            or payload.get("message_id", "")
        )
        conv_id = (
            payload.get("conversation_id", "")
            or payload.get("conversationId", "")
            or msg_obj.get("conversation_id", "")
            or msg_obj.get("conversationId", "")
        )

        print(f"📥 Wabery Webhook Received: text='{text}' | from={phone} | msg_id={msg_id} | conv={conv_id}")

        if not text:
            return {"status": "ok", "received": True}

        # Dedup: skip if polling listener already processed this message
        from channels.wabery_listener import message_dedup
        dedup_key = msg_id or conv_id or f"wh_{hash(text + phone)}"
        if message_dedup.is_seen(dedup_key):
            print(f"⏭️ Wabery Webhook: Message already processed by polling listener, skipping.")
            return {"status": "ok", "received": True, "deduplicated": True}
        message_dedup.mark_seen(dedup_key)

        # Find customer from phone (safe lookup)
        customer = {
            "id": "cust_001", "name": "Gagan Singhal", "preferred_language": "hinglish", "phone": phone
        }
        try:
            phone_clean = phone.replace("+91", "").replace("+", "").strip()
            phone_variants = [phone, f"+91{phone_clean}", phone_clean]
            customers = supabase.table("customers").select("*").in_("phone", phone_variants).execute()
            if customers.data:
                customer = customers.data[0]
        except Exception as db_err:
            print(f"⚠️ Wabery Webhook: Customer DB lookup error: {db_err}. Using default profile.")

        # Run Gemini AI Conversational Recovery Agent
        from agents.conversational_agent import handle_customer_reply
        result = await handle_customer_reply(customer, text, channel="whatsapp", message_id=dedup_key)
        reply_text = result.get("reply", "")
        intent = result.get("intent", "other")

        # Send response directly back to customer on WhatsApp!
        if reply_text:
            from channels.wabery_client import send_whatsapp as send_wabery_msg
            send_wabery_msg(phone, reply_text, conv_id=conv_id)
            print(f"🚀 Wabery Webhook: Intent={intent} | Reply sent: '{reply_text[:80]}...'")

        return {"status": "ok", "received": True, "intent": intent, "reply": reply_text}
    except Exception as e:
        print(f"⚠️ Wabery webhook error: {e}")
        import traceback
        traceback.print_exc()
        return {"status": "ok", "error": str(e)}





