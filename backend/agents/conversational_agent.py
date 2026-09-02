"""
RecoverAI — Agent: Conversational Intelligence
Generates empathetic, context-aware, hyper-personalized recovery replies using Gemini AI.
Considers transaction history, product details, customer segment, decline reason, and promise dates.
"""

import json
import re
from datetime import datetime, timedelta, date
import google.generativeai as genai
from config import settings
from database import supabase, insert_promise, insert_channel_message, insert_recovery_action

genai.configure(api_key=settings.google_api_key)

# Fast & reliable active Gemini models (sub-3s latency)
MODELS_TO_TRY = [
    "gemini-3.1-flash-lite",
    "gemini-3.6-flash",
    "gemini-3.5-flash-lite",
    "gemini-flash-lite-latest",
    "gemini-flash-latest"
]


def _resolve_relative_date(text: str) -> str:
    """Robust fallback date resolver for Hinglish / English / Hindi phrases."""
    text_lower = (text or "").lower().strip()
    today = datetime.utcnow().date()

    # 1. Direct offset words
    if "tomorrow" in text_lower or "kal" in text_lower:
        return (today + timedelta(days=1)).isoformat()
    if "parso" in text_lower or "day after tomorrow" in text_lower:
        return (today + timedelta(days=2)).isoformat()
    if "next week" in text_lower or "agla hafta" in text_lower or "agle hafte" in text_lower:
        return (today + timedelta(days=7)).isoformat()

    # 2. 'after N days' or 'N din baad' or 'in N days'
    m_days = re.search(r"(?:after|in)\s+(\d+)\s+days?", text_lower) or re.search(r"(\d+)\s+din\s+baad", text_lower)
    if m_days:
        days = int(m_days.group(1))
        return (today + timedelta(days=days)).isoformat()

    # 3. Weekday matching
    weekdays = {
        "monday": 0, "somwar": 0,
        "tuesday": 1, "mangalwar": 1,
        "wednesday": 2, "budhwar": 2,
        "thursday": 3, "guruvar": 3, "veervar": 3,
        "friday": 4, "shukrawar": 4,
        "saturday": 5, "shaniwar": 5,
        "sunday": 6, "ravivar": 6, "itwar": 6
    }
    for wname, wday in weekdays.items():
        if wname in text_lower:
            curr_wday = today.weekday()
            days_ahead = (wday - curr_wday) % 7
            if days_ahead == 0:
                days_ahead = 7  # next occurrence
            return (today + timedelta(days=days_ahead)).isoformat()

    # 4. Specific Month Date (e.g. 10 sept, 22 september, 5 oct)
    months = {
        "jan": 1, "january": 1, "feb": 2, "february": 2, "mar": 3, "march": 3,
        "apr": 4, "april": 4, "may": 5, "jun": 6, "june": 6, "jul": 7, "july": 7,
        "aug": 8, "august": 8, "sep": 9, "sept": 9, "september": 9, "oct": 10, "october": 10,
        "nov": 11, "november": 11, "dec": 12, "december": 12
    }
    m_date = re.search(r"(\d{1,2})(?:st|nd|rd|th)?\s+([a-zA-Z]+)", text_lower) or re.search(r"([a-zA-Z]+)\s+(\d{1,2})(?:st|nd|rd|th)?", text_lower)
    if m_date:
        g1, g2 = m_date.groups()
        day_str, month_str = (g1, g2) if g1.isdigit() else (g2, g1)
        month_str = month_str.lower()
        if month_str in months:
            day_num = int(day_str)
            month_num = months[month_str]
            year = today.year
            if month_num < today.month or (month_num == today.month and day_num < today.day):
                year += 1
            try:
                return date(year, month_num, day_num).isoformat()
            except Exception:
                pass

    return (today + timedelta(days=2)).isoformat()


def _call_gemini_json(prompt: str) -> dict:
    """Call Gemini models with fallback chain for pure LLM intent and date extraction."""
    last_err = None
    for model_name in MODELS_TO_TRY:
        try:
            m = genai.GenerativeModel(
                model_name=model_name,
                generation_config={"response_mime_type": "application/json"}
            )
            resp = m.generate_content(prompt)
            if resp and resp.text:
                raw = resp.text.strip()
                raw = re.sub(r"^```json\s*", "", raw)
                raw = re.sub(r"^```\s*", "", raw)
                raw = re.sub(r"\s*```$", "", raw)
                return json.loads(raw)
        except Exception as err:
            last_err = err
            continue

    print(f"❌ [Conversational Agent] LLM chain error: {last_err}")
    return {}


async def handle_customer_reply(customer: dict, user_message: str, channel: str = "whatsapp", message_id: str = "") -> dict:
    """Intelligently process any customer reply, generate Gemini response, and update Supabase."""
    customer_id = customer.get("id", "cust_001")
    first_name = customer.get("name", "Gagan Singhal").split()[0]
    language = customer.get("preferred_language", "hinglish")
    phone = customer.get("phone", "+918077344252")

    # 1. Fetch latest active transaction
    txns = supabase.table("transactions") \
        .select("*") \
        .eq("customer_id", customer_id) \
        .order("created_at", desc=True) \
        .limit(1) \
        .execute()
    txn = txns.data[0] if txns.data else None

    # Fallback to any recent transaction if customer_id didn't match directly
    if not txn:
        fallback_txns = supabase.table("transactions") \
            .select("*") \
            .order("created_at", desc=True) \
            .limit(1) \
            .execute()
        txn = fallback_txns.data[0] if fallback_txns.data else None

    product_name = txn.get("product_name", "your order") if txn else "your order"
    amount_val = txn.get("amount", 429900) if txn else 429900
    amount_str = f"₹{amount_val // 100}"
    failure_reason = txn.get("failure_reason", "card_expired") if txn else "payment failure"
    payment_link = "https://rzp.io/i/demo"

    # Fetch latest generated Razorpay link if available
    if txn:
        try:
            msgs = supabase.table("channel_messages") \
                .select("payment_link_url") \
                .eq("transaction_id", txn["id"]) \
                .neq("payment_link_url", "null") \
                .order("created_at", desc=True) \
                .limit(1) \
                .execute()
            if msgs.data and msgs.data[0].get("payment_link_url"):
                fetched_link = msgs.data[0]["payment_link_url"]
                # Only use if it's a real link (not empty or placeholder)
                if fetched_link and fetched_link.startswith("http"):
                    payment_link = fetched_link
        except Exception:
            pass  # Keep default link on any DB error

    # 2. Prompt LLM for Intent Classification, Promise Date Extraction, and Empathic Reply
    today_iso = datetime.utcnow().strftime('%Y-%m-%d')
    current_year = datetime.utcnow().year
    
    prompt = f"""You are the Conversational AI Revenue Recovery Agent for StyleBazaar (RecoverAI).
A customer replied to our automated payment failure communication.

Today's Date: {today_iso} (Year: {current_year})

Customer Profile:
- Name: {customer.get('name', 'Gagan Singhal')}
- Preferred Language: {language}
- Order: {product_name} ({amount_str})
- Failure Reason: {failure_reason}
- 1-Click Payment Link: {payment_link}
- Customer Reply: "{user_message}"

Analyze the customer's reply using Natural Language Understanding and extract:
1. "intent": Exactly one of:
   - "promise_to_pay": Customer states when they will pay (e.g. "I will pay on 10 sept", "kal pay karunga", "next week", "Friday", "salary ke baad", "after 2 days").
   - "payment_done": Customer states they have already paid or completed it (e.g. "already paid", "done", "ho gaya", "kar diya").
   - "will_pay_now": Customer asks for link or wants to pay immediately (e.g. "send link", "abhi karta hu", "give upi link").
   - "need_help": Customer asks why it failed, has questions, or issues.
   - "opt_out": Customer wants to stop receiving messages (e.g. "STOP", "don't message").
   - "other": General greetings or chit-chat.

2. "promise_date_iso": 
   - If intent is "promise_to_pay", carefully compute and output the EXACT target date in "YYYY-MM-DD" format.
   - For example:
     * If user says "10 sept" or "10 september", output "{current_year}-09-10".
     * If user says "tomorrow" or "kal", compute today + 1 day.
     * If user says a day name like "Thursday" or "Guruvar", compute the upcoming date for that day.
     * If intent is NOT promise_to_pay, output null.

3. "reply": A warm, natural, human-like reply in {language} (1 to 2 sentences with polite emojis).
   - If promise_to_pay: Warmly acknowledge their specified date and reassure them their payment link stays active.
   - If payment_done: Congratulate them and confirm their order is being processed.
   - If will_pay_now: Share the 1-click link excitedly.
   - If need_help: Explain politely and provide alternative options with the link.
   - If opt_out: Confirm respectfully that they will receive no further messages.
   - If other: Be helpful and share the payment link.

Return ONLY a JSON object matching this schema:
{{
  "intent": "promise_to_pay" | "payment_done" | "will_pay_now" | "need_help" | "opt_out" | "other",
  "promise_date_iso": "YYYY-MM-DD" or null,
  "reply": "string"
}}"""

    parsed = _call_gemini_json(prompt)
    intent = parsed.get("intent", "other")
    promise_date_str = parsed.get("promise_date_iso")
    reply_text = parsed.get("reply", "")

    # If intent is promise_to_pay but date was not parsed by LLM, use robust Python resolver
    if intent == "promise_to_pay" and not promise_date_str:
        promise_date_str = _resolve_relative_date(user_message)

    # Fallback message if LLM produced empty reply
    if not reply_text:
        if intent == "promise_to_pay":
            reply_text = f"Koi baat nahi {first_name}! 🙏 Hum aapko {promise_date_str or 'specified date'} ko remind karenge. Payment link active rahega: {payment_link} 👍"
        elif intent == "payment_done":
            reply_text = f"Shukriya {first_name}! 🎉 Aapka {amount_str} ka payment confirm ho gaya hai. Aapka order process ho raha hai! 👍"
        elif intent == "will_pay_now":
            reply_text = f"Bahut badhiya {first_name}! 🎉 Yeh raha aapka 1-click payment link: {payment_link}"
        else:
            reply_text = f"Hi {first_name}! 🙏 Order complete karne ke liye yahan click karein: {payment_link}"

    # Clean date if ISO format includes time
    if promise_date_str and "T" in promise_date_str:
        promise_date_str = promise_date_str.split("T")[0]

    # 3. Agent Lifecycle Updates in Supabase
    transaction_id = txn["id"] if txn else None

    if intent == "payment_done":
        if txn:
            supabase.table("transactions").update({
                "recovery_status": "recovered",
                "recovery_amount": amount_val,
                "recovered_at": datetime.utcnow().isoformat(),
            }).eq("id", txn["id"]).execute()

        # Log recovery in audit trail so it shows in the Live Agent Feed
        await insert_recovery_action({
            "transaction_id": transaction_id,
            "agent": "executor",
            "action": "whatsapp_recovery_confirmed",
            "details": {
                "channel": channel,
                "customer_message": user_message[:200],
                "intent": intent,
                "recovery_successful": True,
                "amount_recovered": amount_val,
                "payment_link": payment_link,
            },
            "result": "success",
        })

        # Trigger Agent 6 (Analyst) to learn from WhatsApp payment recovery
        if transaction_id:
            import asyncio
            from agents.analyst import trigger_post_recovery_analysis
            asyncio.create_task(trigger_post_recovery_analysis(transaction_id, amount_val))

    elif intent == "promise_to_pay":
        # Ensure promise_date is in YYYY-MM-DD format
        if promise_date_str and "T" in promise_date_str:
            promise_date_str = promise_date_str.split("T")[0]

        if txn:
            supabase.table("transactions").update({
                "recovery_status": "in_progress",
            }).eq("id", txn["id"]).execute()

        # Insert promise in Supabase (LLM-extracted target date)
        await insert_promise({
            "customer_id": customer_id,
            "transaction_id": transaction_id,
            "promise_date": promise_date_str,
            "promise_amount": amount_val,
            "status": "promised",
            "whatsapp_message_sid": message_id or "wab_reply",
        })

        # Log promise in audit trail
        await insert_recovery_action({
            "transaction_id": transaction_id,
            "agent": "executor",
            "action": "promise_to_pay_received",
            "details": {
                "channel": channel,
                "customer_message": user_message[:200],
                "intent": intent,
                "promise_date": promise_date_str,
                "promise_amount": amount_val,
            },
            "result": "success",
        })

    elif intent == "opt_out":
        supabase.table("customers").update({"opted_out": True}).eq("id", customer_id).execute()

        # Log opt-out in audit trail
        await insert_recovery_action({
            "transaction_id": transaction_id,
            "agent": "compliance",
            "action": "customer_opted_out",
            "details": {
                "channel": channel,
                "customer_message": user_message[:200],
                "intent": intent,
                "customer_id": customer_id,
            },
            "result": "blocked",
        })

    elif intent == "will_pay_now":
        # Log intent in audit trail
        await insert_recovery_action({
            "transaction_id": transaction_id,
            "agent": "executor",
            "action": "payment_link_requested",
            "details": {
                "channel": channel,
                "customer_message": user_message[:200],
                "intent": intent,
                "payment_link": payment_link,
            },
            "result": "success",
        })

    elif intent == "need_help":
        # Log help request in audit trail
        await insert_recovery_action({
            "transaction_id": transaction_id,
            "agent": "diagnostician",
            "action": "customer_help_request",
            "details": {
                "channel": channel,
                "customer_message": user_message[:200],
                "intent": intent,
                "failure_reason": failure_reason,
            },
            "result": "success",
        })

    # 4. Save audit log & channel message
    await insert_channel_message({
        "transaction_id": transaction_id,
        "customer_id": customer_id,
        "channel": channel,
        "language": language,
        "message_content": f"INCOMING: {user_message[:200]} | AI_REPLY: {reply_text[:200]}",
        "external_id": message_id or "conv_reply",
        "status": "received",
    })

    return {
        "intent": intent,
        "reply": reply_text,
        "promise_date": promise_date_str,
        "recovered": intent == "payment_done",
        "transaction_id": transaction_id,
    }


