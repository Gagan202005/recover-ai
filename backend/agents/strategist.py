"""
RecoverAI — Agent 3: STRATEGIST
Intelligent Recovery Planning using Gemini AI + RAG playbook + A/B testing + Thompson Sampling.
"""

import time
import json
import re
import random
from datetime import datetime
from agents.state import RecoveryState
from database import insert_recovery_action, supabase
from rag.pinecone_client import query_playbook
from channels.message_templates import select_language, render_template
import google.generativeai as genai
from config import settings

genai.configure(api_key=settings.google_api_key)
model = genai.GenerativeModel(settings.gemini_model)


TONE_MAP = {
    "vip": "warm_friendly", "regular": "friendly", "new": "gentle",
    "b2b": "professional", "subscription": "helpful",
}


async def strategist_node(state: RecoveryState) -> dict:
    """Strategist agent: plan recovery strategy with Gemini AI + RAG + A/B testing."""
    start_time = time.time()

    diagnosis = state.get("diagnosis", {})
    root_cause = diagnosis.get("root_cause", "unknown")
    confidence = diagnosis.get("confidence", 0.5)
    is_outage = diagnosis.get("is_outage", False)
    customer_ctx = state.get("customer_context", {})
    segment = customer_ctx.get("segment", "regular")
    preferred_channel = customer_ctx.get("preferred_channel", "")
    preferred_language = customer_ctx.get("preferred_language", "")

    # 1. RAG query — playbook (similar past successful cases)
    rag_playbook = []
    rag_citations = []
    try:
        rag_playbook = await query_playbook(
            failure_type=root_cause,
            amount=state["amount"],
            segment=segment,
            bank=state.get("bank", ""),
            method=state.get("method", ""),
            channel=preferred_channel,
        )
        rag_citations = [{"source": "KB3:playbook", "content": r["content"][:200], "score": r["score"]} for r in rag_playbook[:3]]
    except Exception as e:
        rag_citations = [{"source": "KB3:playbook", "error": str(e)}]

    # 2. Language selection
    language = select_language({"preferred_language": preferred_language, "city": customer_ctx.get("city", "")})

    # 3. Tone based on segment
    tone = TONE_MAP.get(segment, "friendly")

    # 4. Build context for Gemini AI strategy inference
    playbook_context = "\n".join([r["content"] for r in rag_playbook[:3]]) if rag_playbook else "No past recovery cases found yet."

    prompt = f"""You are the Recovery Strategist AI for a payment recovery system.
Based on the failure diagnosis, customer profile, and past playbook data, recommend the BEST recovery strategy.

FAILURE DIAGNOSIS:
- Root Cause: {root_cause}
- Confidence: {confidence}
- Is Bank Outage: {is_outage}
- Bank: {state.get('bank', 'unknown')}
- Payment Method: {state.get('method', 'card')}
- Error Code: {state.get('error_code', 'N/A')}
- Amount: ₹{state['amount'] // 100}

CUSTOMER PROFILE:
- Segment: {segment} (vip/regular/new/b2b/subscription)
- Preferred Channel: {preferred_channel or 'none set'}
- Preferred Language: {preferred_language or 'none set'}
- On DND: {customer_ctx.get('on_dnd', False)}
- City: {customer_ctx.get('city', 'unknown')}

PAST SUCCESSFUL RECOVERY CASES (RAG Playbook):
{playbook_context}

Recommend a strategy as JSON:
{{
  "primary_channel": "whatsapp|sms|email|voice|auto_retry",
  "fallback_channel": "whatsapp|sms|email|voice",
  "delay": "0|1h|2h|4h|24h",
  "reasoning": "1-2 sentence explanation of why this channel + timing",
  "rail_recommendation": "null or string suggesting alternate payment rail if card/UPI failed",
  "dynamic_incentive": "null or string like '10% off coupon' or 'EMI option' if applicable",
  "voice_script": "Spoken AI voice reminder script in Hinglish/English for phone call if channel is voice (or null)"
}}

KEY RULES:
- For bank outages (is_outage=true): MUST use auto_retry with 2h delay, customers can't do anything during bank downtime
- For bank_decline (not outage): MUST use auto_retry with 0 delay first (banks often approve on immediate retry), fallback to sms with payment link
- For card_expired/auth_failed: WhatsApp is best (1-click payment link), use SMS as fallback
- For invoice_overdue (B2B Invoice Overdue): Primary Step 1 MUST be Voice Call (AI phone reminder directly to accounts/finance). Generate a customized spoken 'voice_script' in Hinglish mentioning customer name, overdue amount, invoice item, and merchant. Step 2 is Email with formal invoice & payment link.
- For checkout_abandoned (checkout drop-off): Primary Step 1 MUST be Email (gentle reminder with cart summary and 1-click payment link). Recommend the best fallback channel (whatsapp or sms), delay, and time-sensitive incentive (e.g. discount coupon) for step 2.
- For insufficient_funds: WhatsApp with EMI/split-pay option, or delay until likely salary date
- For auto_debit_failed: auto_retry first, then WhatsApp with re-authorization link
- For network_timeout: auto_retry immediately (90% succeed on retry)
- If customer prefers a channel, respect it UNLESS the root cause requires auto_retry, checkout_abandoned email-first, or invoice_overdue voice-first rule
- DND customers cannot receive SMS/voice — use email or WhatsApp instead

Respond ONLY with valid JSON. No markdown code blocks."""

    # Default strategy (used if Gemini fails)
    channel = "whatsapp"
    fallback = "email"
    delay = "0"
    rail_recommendation = None
    dynamic_incentive = None
    voice_script = None
    gemini_reasoning = ""

    try:
        import asyncio
        response = await asyncio.to_thread(model.generate_content, prompt)
        raw = response.text.strip()
        raw = re.sub(r"^```json\s*", "", raw)
        raw = re.sub(r"^```\s*", "", raw)
        raw = re.sub(r"\s*```$", "", raw)
        strategy_llm = json.loads(raw)

        channel = strategy_llm.get("primary_channel", "whatsapp")
        fallback = strategy_llm.get("fallback_channel", "email")
        delay = strategy_llm.get("delay", "0")
        rail_recommendation = strategy_llm.get("rail_recommendation")
        dynamic_incentive = strategy_llm.get("dynamic_incentive")
        voice_script = strategy_llm.get("voice_script")
        gemini_reasoning = strategy_llm.get("reasoning", "")

        # For B2B invoice overdue, enforce step 1 as voice call with dynamic script
        if root_cause == "invoice_overdue":
            channel = "voice"
            fallback = "email"
            if not voice_script:
                cust_name = customer_ctx.get("name", "Gagan Singhal")
                amt_str = f"{state['amount'] // 100:,}"
                prod = state.get("product_name", "B2B Invoice")
                voice_script = f"Namaste {cust_name} ji! Main {settings.merchant_name} RecoverAI se bol raha hoon. Aapke {prod} ke {amt_str} rupaye ka B2B invoice payment overdue hai. Kripya diye gaye payment link se payment complete karein. Dhanyavaad!"

        # For checkout drop-off (checkout_abandoned), enforce step 1 as email, step 2 as LLM fallback
        if root_cause == "checkout_abandoned":
            channel = "email"
            if not fallback or fallback == "email":
                fallback = "whatsapp"

        # Validate channel is a known value
        valid_channels = {"whatsapp", "sms", "email", "voice", "auto_retry", "payment_link"}
        if channel not in valid_channels:
            channel = "whatsapp"
        if fallback not in valid_channels:
            fallback = "email"

    except Exception as e:
        print(f"⚠️ [Strategist] Gemini fallback: {e}")
        # Intelligent fallback based on diagnosis (not just a static map)
        if is_outage:
            channel, fallback, delay = "auto_retry", "whatsapp", "2h"
        elif root_cause == "bank_decline":
            channel, fallback, delay = "auto_retry", "sms", "0"
        elif root_cause == "network_timeout":
            channel, fallback, delay = "auto_retry", "payment_link", "0"
        elif root_cause in ("card_expired", "auth_failed"):
            channel, fallback, delay = "whatsapp", "sms", "0"
        elif root_cause == "checkout_abandoned":
            channel, fallback, delay = "email", "whatsapp", "0"
        elif root_cause == "invoice_overdue":
            channel, fallback, delay = "voice", "email", "0"
            cust_name = customer_ctx.get("name", "Gagan Singhal")
            amt_str = f"{state['amount'] // 100:,}"
            prod = state.get("product_name", "B2B Invoice")
            voice_script = f"Namaste {cust_name} ji! Main {settings.merchant_name} RecoverAI se bol raha hoon. Aapke {prod} ke {amt_str} rupaye ka B2B invoice overdue hai. Dhanyavaad!"
        elif root_cause == "insufficient_funds":
            channel, fallback, delay = "whatsapp", "sms", "0"
            dynamic_incentive = "Split-payment & Pay-Later / No-Cost EMI options enabled on checkout link."
        elif root_cause in ("auto_debit_failed", "mandate_expired"):
            channel, fallback, delay = "auto_retry" if root_cause == "auto_debit_failed" else "whatsapp", "whatsapp", "4h" if root_cause == "auto_debit_failed" else "0"
        else:
            channel, fallback, delay = "whatsapp", "email", "0"

    # 5. A/B test assignment (Thompson Sampling)
    ab_experiment = None
    try:
        tests = supabase.table("ab_tests").select("*").eq("failure_type", root_cause).eq("is_significant", False).execute()
        if tests.data:
            test = tests.data[0]
            alpha_a = test.get("variant_a_successes", 1) + 1
            beta_a = test.get("variant_a_trials", 1) - test.get("variant_a_successes", 0) + 1
            alpha_b = test.get("variant_b_successes", 1) + 1
            beta_b = test.get("variant_b_trials", 1) - test.get("variant_b_successes", 0) + 1
            sample_a = random.betavariate(max(alpha_a, 1), max(beta_a, 1))
            sample_b = random.betavariate(max(alpha_b, 1), max(beta_b, 1))
            if sample_b > sample_a:
                channel = test["variant_b"]
            else:
                channel = test["variant_a"]
            ab_experiment = {"test_id": test["id"], "variant": channel}
    except Exception:
        pass

    # 6. Hard override: bank_decline and network_timeout MUST use auto_retry
    # (banks often approve on immediate retry — this is the #1 recovery strategy for declines)
    auto_retry_causes = {"bank_decline", "network_timeout", "auto_debit_failed"}
    if root_cause in auto_retry_causes and not is_outage:
        channel = "auto_retry"
        fallback = "sms" if root_cause == "bank_decline" else fallback
        delay = "0"
        if not rail_recommendation and state.get("method") == "card":
            rail_recommendation = f"Card declined by {state.get('bank', 'bank')}. Auto-retry via same rail + generate UPI/Netbanking payment link as fallback."

    # 7. Hard override: outage MUST use auto_retry with delay
    if is_outage:
        channel = "auto_retry"
        delay = "2h"
        if not rail_recommendation:
            rail_recommendation = f"Active downtime on {state.get('bank', 'bank')}. Pause auto-retries for 2h; fallback to alternate UPI rails."

    # 8. Respect customer preference (UNLESS auto_retry, checkout_abandoned, or invoice_overdue voice rule is required)
    if preferred_channel and preferred_channel != channel and channel != "auto_retry" and root_cause not in ("checkout_abandoned", "invoice_overdue"):
        channel = preferred_channel

    # 9. B2B Invoice overdue voice script check
    if root_cause == "invoice_overdue":
        channel = "voice"
        fallback = "email"

    # 10. Checkout abandoned incentive
    if root_cause == "checkout_abandoned":
        channel = "email"  # Guarantee Step 1 is Email
        if not dynamic_incentive:
            discount = 10 if state.get("amount", 0) >= 300000 else 5
            dynamic_incentive = f"{discount}% off coupon code (RECOVER{discount}) attached to recovery email & payment link."

    # 11. Card failure rail recommendation
    if state.get("method") == "card" and root_cause in ("bank_decline", "card_expired", "auth_failed") and not rail_recommendation:
        rail_recommendation = "Failing on Card rail. Generate 1-click Razorpay UPI QR & Netbanking payment link."

    strategy = {
        "steps": [
            {"step": 1, "action": channel, "delay": delay},
            {"step": 2, "action": fallback, "delay": "24h"},
        ],
        "channel": channel,
        "fallback": fallback,
        "timing": delay,
        "language": language,
        "tone": tone,
        "rail_recommendation": rail_recommendation,
        "dynamic_incentive": dynamic_incentive,
        "voice_script": voice_script,
        "ab_experiment": ab_experiment,
        "gemini_reasoning": gemini_reasoning,
        "rag_citations": rag_citations,
    }

    duration_ms = int((time.time() - start_time) * 1000)

    await insert_recovery_action({
        "transaction_id": state["transaction_id"],
        "agent": "strategist",
        "action": "planned",
        "details": {k: v for k, v in strategy.items() if k != "rag_citations"},
        "rag_citations": rag_citations,
        "result": "success",
        "duration_ms": duration_ms,
    })

    return {
        "strategy": strategy,
        "audit_trail": state.get("audit_trail", []) + [{"agent": "strategist", "action": "planned", "ts": datetime.utcnow().isoformat()}],
    }
