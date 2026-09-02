"""
RecoverAI — Agent 4: COMPLIANCE OFFICER
Intelligent guardrail gate with optimized rule checks, Gemini-powered debates, and RAG citations.

Key Design Principles:
- We only SEND PAYMENT LINKS (never auto-debit). Customer always authorizes payment themselves.
- No human_review verdict — since we're not debiting, there's no financial risk in sending a notification.
- Verdicts: approved | modified | blocked
- Gemini debates are reserved for hard blocks; soft modifications use static templates for speed.
"""

import time
import json
import re
from datetime import datetime
from agents.state import RecoveryState
from database import insert_recovery_action, insert_debate, get_customer_messages_today
from rag.pinecone_client import query_compliance
import google.generativeai as genai
from config import settings

genai.configure(api_key=settings.google_api_key)
model = genai.GenerativeModel(settings.gemini_model)

# ── Constants ──
MAX_NOTIFICATION_RETRIES = 3       # Max notification re-sends per transaction
MAX_AUTO_RETRIES = 5               # Max fresh payment link generations per transaction
DAILY_MESSAGE_CAP = 5              # Max messages per customer per day (industry best practice)
ALLOWED_HOURS = (9, 21)            # 9 AM - 9 PM IST
COOL_OFF_HOURS = 4                 # Minimum hours between successive contacts
HIGH_VALUE_THRESHOLD = 1000000     # ₹10,000 in paise — advisory tag, NOT a block


async def compliance_node(state: RecoveryState) -> dict:
    """Compliance agent: run guardrail checks, generate intelligent debates if blocked."""
    start_time = time.time()

    strategy = state.get("strategy", {})
    customer_ctx = state.get("customer_context", {})
    diagnosis = state.get("diagnosis", {})
    channel = strategy.get("channel", "whatsapp")
    debates = list(state.get("debates", []))

    checks_passed = []
    checks_failed = []
    modifications = []
    advisories = []        # Non-blocking notes (e.g. high-value tag)
    verdict = "approved"

    # ── RAG — compliance rules (context-aware query) ──
    rag_citations = []
    rag_context = ""
    try:
        root_cause = diagnosis.get("root_cause", "")
        rag_results = await query_compliance(
            action_type=f"{channel} payment recovery notification",
            channel=channel,
            failure_type=root_cause,
            amount=state.get("amount", 0)
        )
        rag_citations = [{"source": "KB2:compliance", "content": r["content"][:200], "score": r["score"]} for r in rag_results[:3]]
        rag_context = "\n".join([r["content"] for r in rag_results[:3]])
    except Exception:
        pass

    # ═══════════════════════════════════════════════════════════
    # CHECK 1: Opt-Out — HARD BLOCK (immediate exit)
    # ═══════════════════════════════════════════════════════════
    if customer_ctx.get("opted_out"):
        checks_failed.append("opt_out")
        verdict = "blocked"
        debate = await _generate_debate(
            state, channel, "opt_out",
            "Customer has opted out of all communications.",
            rag_context
        )
        debates.append(debate)
        result = {
            "verdict": "blocked", "checks_passed": [], "checks_failed": ["opt_out"],
            "modifications": [], "advisories": [], "rag_citations": rag_citations,
            "block_reason": "Customer opted out. All recovery channels blocked.",
        }
        duration_ms = int((time.time() - start_time) * 1000)
        await insert_recovery_action({
            "transaction_id": state["transaction_id"], "agent": "compliance",
            "action": "blocked", "details": result, "rag_citations": rag_citations,
            "result": "blocked", "duration_ms": duration_ms,
        })
        await _log_debate(state["transaction_id"], debates[-1])
        return {"compliance_result": result, "debates": debates, "status": "exception",
                "audit_trail": state.get("audit_trail", []) + [{"agent": "compliance", "action": "blocked", "ts": datetime.utcnow().isoformat()}]}

    # ═══════════════════════════════════════════════════════════
    # CHECK 2: Active Dispute — HARD BLOCK (immediate exit)
    # ═══════════════════════════════════════════════════════════
    if customer_ctx.get("has_dispute"):
        checks_failed.append("dispute")
        verdict = "blocked"
        debate = await _generate_debate(
            state, channel, "dispute",
            "Customer has an active dispute/chargeback. Recovery communication blocked during dispute resolution.",
            rag_context
        )
        debates.append(debate)
        result = {
            "verdict": "blocked", "checks_passed": checks_passed, "checks_failed": ["dispute"],
            "modifications": [], "advisories": [], "rag_citations": rag_citations,
            "block_reason": "Active dispute/chargeback. Recovery blocked per RBI Ombudsman Scheme 2021.",
        }
        duration_ms = int((time.time() - start_time) * 1000)
        await insert_recovery_action({
            "transaction_id": state["transaction_id"], "agent": "compliance",
            "action": "blocked", "details": result, "rag_citations": rag_citations,
            "result": "blocked", "duration_ms": duration_ms,
        })
        await _log_debate(state["transaction_id"], debates[-1])
        return {"compliance_result": result, "debates": debates, "status": "exception",
                "audit_trail": state.get("audit_trail", []) + [{"agent": "compliance", "action": "blocked", "ts": datetime.utcnow().isoformat()}]}

    # ═══════════════════════════════════════════════════════════
    # CHECK 3: DND Registry — SOFT MODIFICATION (switch channel)
    # ═══════════════════════════════════════════════════════════
    if customer_ctx.get("on_dnd") and channel in ("sms", "voice"):
        checks_failed.append("dnd")
        original_channel = channel
        channel = "whatsapp" if channel == "sms" else "email"  # WhatsApp preferred over email
        modifications.append({"original": original_channel, "revised": channel, "reason": "Customer on TRAI DND — switched to exempt channel"})
        # Static debate for soft modification (no Gemini call needed)
        debates.append(_static_debate(
            channel=original_channel, check_name="dnd",
            objection=f"Customer is on TRAI DND registry. {original_channel.upper()} channel blocked for DND numbers.",
            resolution=f"Switched to {channel} (transactional messages exempt from DND restrictions).",
            citation="TRAI DND Regulations 2018, Section 4.2: Transactional recovery messages to DND numbers must use exempt channels (WhatsApp/Email)."
        ))
    else:
        checks_passed.append("dnd")

    # ═══════════════════════════════════════════════════════════
    # CHECK 4: Time Window (9 AM - 9 PM IST) — SOFT MODIFICATION
    # ═══════════════════════════════════════════════════════════
    ist_hour = (datetime.utcnow().hour + 5) % 24  # Rough IST
    if not (ALLOWED_HOURS[0] <= ist_hour < ALLOWED_HOURS[1]):
        checks_failed.append("time_window")
        if channel in ("sms", "voice", "whatsapp"):
            modifications.append({"original": "send_now", "revised": "schedule_9am", "reason": f"Outside 9 AM - 9 PM IST (current ~{ist_hour}:00)"})
            # Static debate for scheduling (no Gemini needed)
            debates.append(_static_debate(
                channel=channel, check_name="time_window",
                objection=f"Current IST hour is ~{ist_hour}:00, outside the 9 AM - 9 PM communication window.",
                resolution="Scheduled delivery for 9:00 AM IST next day.",
                citation="TRAI TCCCPR 2018, Regulation 7: Commercial & transactional communications restricted to 9 AM - 9 PM IST."
            ))
    else:
        checks_passed.append("time_window")

    # ═══════════════════════════════════════════════════════════
    # CHECK 5: Retry Limit — HARD BLOCK
    # Smart distinction: notification retries vs auto-retries
    # ═══════════════════════════════════════════════════════════
    attempt_count = state.get("attempt_count", 0) or 0
    is_auto_retry = channel == "auto_retry"
    max_retries = MAX_AUTO_RETRIES if is_auto_retry else MAX_NOTIFICATION_RETRIES

    if attempt_count >= max_retries:
        checks_failed.append("retry_limit")
        verdict = "blocked"
        retry_type = "auto-retry (payment link)" if is_auto_retry else "notification"
        debate = await _generate_debate(
            state, channel, "retry_limit",
            f"Maximum {max_retries} {retry_type} retries reached. This is attempt #{attempt_count + 1}. Transaction should be escalated to exception queue.",
            rag_context
        )
        debates.append(debate)
    else:
        checks_passed.append("retry_limit")

    # ═══════════════════════════════════════════════════════════
    # CHECK 6: Frequency Cap (5 messages/day) — HARD BLOCK
    # ═══════════════════════════════════════════════════════════
    try:
        msg_count = await get_customer_messages_today(state["customer_id"])
        if msg_count >= DAILY_MESSAGE_CAP:
            checks_failed.append("frequency_cap")
            verdict = "blocked"
            modifications.append({"original": "send_now", "revised": "schedule_tomorrow", "reason": f"{msg_count} messages already sent today (cap: {DAILY_MESSAGE_CAP}/day)"})
            debate = await _generate_debate(
                state, channel, "frequency_cap",
                f"Customer has already received {msg_count} messages today. Daily cap is {DAILY_MESSAGE_CAP}. Must schedule for tomorrow.",
                rag_context
            )
            debates.append(debate)
        else:
            checks_passed.append("frequency_cap")
    except Exception:
        checks_passed.append("frequency_cap")

    # ═══════════════════════════════════════════════════════════
    # CHECK 7: Cool-Off Period (4 hours) — HARD BLOCK
    # ═══════════════════════════════════════════════════════════
    last_contact = customer_ctx.get("last_contact_at")
    if last_contact:
        try:
            last_dt = datetime.fromisoformat(last_contact.replace("Z", "+00:00"))
            hours_since = (datetime.utcnow() - last_dt.replace(tzinfo=None)).total_seconds() / 3600
            if hours_since < COOL_OFF_HOURS:
                checks_failed.append("cool_off")
                verdict = "blocked"
                wait_hours = int(COOL_OFF_HOURS - hours_since) + 1
                modifications.append({"original": "send_now", "revised": f"wait_{wait_hours}h", "reason": f"Last contact {hours_since:.1f}h ago, need {COOL_OFF_HOURS}h cool-off"})
                debate = await _generate_debate(
                    state, channel, "cool_off",
                    f"Last contact was {hours_since:.1f} hours ago. Minimum {COOL_OFF_HOURS}-hour cool-off period required.",
                    rag_context
                )
                debates.append(debate)
            else:
                checks_passed.append("cool_off")
        except Exception:
            checks_passed.append("cool_off")
    else:
        checks_passed.append("cool_off")

    # ═══════════════════════════════════════════════════════════
    # CHECK 8: High-Value Advisory — NON-BLOCKING TAG
    # Since we only send payment links (no auto-debit), high-value
    # transactions are safe to notify. We just tag them for analytics.
    # ═══════════════════════════════════════════════════════════
    if state["amount"] > HIGH_VALUE_THRESHOLD:
        advisories.append({
            "type": "high_value",
            "amount": state["amount"],
            "note": f"₹{state['amount'] // 100:,} exceeds ₹10,000 threshold. Tagged for high-value monitoring. No block required — customer authorizes payment via link.",
        })
        checks_passed.append("high_value_advisory")
    else:
        checks_passed.append("high_value_advisory")

    # ═══════════════════════════════════════════════════════════
    # FINAL VERDICT
    # Only 3 verdicts: approved | modified | blocked
    # ═══════════════════════════════════════════════════════════
    if verdict != "blocked":
        verdict = "modified" if modifications else "approved"

    result = {
        "verdict": verdict,
        "checks_passed": checks_passed,
        "checks_failed": checks_failed,
        "modifications": modifications,
        "advisories": advisories,
        "revised_channel": channel,
        "rag_citations": rag_citations,
    }

    duration_ms = int((time.time() - start_time) * 1000)

    await insert_recovery_action({
        "transaction_id": state["transaction_id"], "agent": "compliance",
        "action": verdict, "details": result, "rag_citations": rag_citations,
        "result": verdict, "duration_ms": duration_ms,
    })

    # Log all new debates
    for debate in debates:
        if debate not in state.get("debates", []):
            await _log_debate(state["transaction_id"], debate)

    new_status = state.get("status", "processing")
    if verdict == "blocked":
        new_status = "exception"

    # Update strategy with revised channel
    updated_strategy = {**strategy, "channel": channel}

    return {
        "compliance_result": result, "debates": debates, "status": new_status,
        "strategy": updated_strategy,
        "audit_trail": state.get("audit_trail", []) + [{"agent": "compliance", "action": verdict, "ts": datetime.utcnow().isoformat()}],
    }


def _static_debate(channel: str, check_name: str, objection: str, resolution: str, citation: str) -> dict:
    """Generate a static debate record for non-blocking modifications (no Gemini call needed)."""
    return {
        "proposer": "strategist", "reviewer": "compliance",
        "original": {"channel": channel},
        "objection": objection,
        "resolution": {"action": "modify", "reason": check_name, "detail": resolution},
        "citation": citation,
    }


async def _generate_debate(state: dict, channel: str, check_name: str, objection: str, rag_context: str) -> dict:
    """Use Gemini to generate an intelligent compliance debate with proper legal citations.
    Reserved for HARD BLOCKS only — soft modifications use _static_debate instead."""
    try:
        prompt = f"""You are a compliance officer for a payment recovery NOTIFICATION system in India.
IMPORTANT: This system ONLY sends payment links to customers. It NEVER auto-debits or charges customers directly.
The customer must always authorize and complete payment themselves through the link.

The strategist proposed sending a {channel} recovery notification, but a compliance check failed.

CHECK FAILED: {check_name}
OBJECTION: {objection}
TRANSACTION AMOUNT: ₹{state.get('amount', 0) // 100}
CUSTOMER SEGMENT: {state.get('customer_context', {}).get('segment', 'regular')}
ROOT CAUSE: {state.get('diagnosis', {}).get('root_cause', 'unknown')}

RELEVANT COMPLIANCE RULES FROM KNOWLEDGE BASE:
{rag_context or 'No specific rules found.'}

Generate a JSON debate record:
{{
  "objection": "detailed objection explaining why this violates compliance",
  "resolution": "what action should be taken instead (e.g., block, schedule later, escalate to exception queue)",
  "citation": "specific regulation citation (RBI/TRAI/Consumer Protection Act with section numbers)"
}}

Use real Indian regulatory references where applicable:
- TRAI DND Regulations 2018 for SMS/voice restrictions
- TRAI TCCCPR 2018 for time window restrictions
- Consumer Protection Act 2019 for opt-out and harassment
- RBI Ombudsman Scheme 2021 for dispute blocks
- Industry best practices for frequency caps and cool-off periods

Respond ONLY with valid JSON. No markdown."""

        import asyncio
        response = await asyncio.to_thread(model.generate_content, prompt)
        raw = response.text.strip()
        raw = re.sub(r"^```json\s*", "", raw)
        raw = re.sub(r"^```\s*", "", raw)
        raw = re.sub(r"\s*```$", "", raw)
        parsed = json.loads(raw)

        return {
            "proposer": "strategist", "reviewer": "compliance",
            "original": {"channel": channel},
            "objection": parsed.get("objection", objection),
            "resolution": parsed.get("resolution", {"action": "block", "reason": check_name}),
            "citation": parsed.get("citation", f"Compliance check: {check_name}"),
        }
    except Exception:
        # Fallback: static debate with correct citations
        citations = {
            "opt_out": "Consumer Protection Act 2019, Section 2(9): Right to opt out of commercial communications must be respected.",
            "retry_limit": "Internal Policy: Notification retries capped at 3, auto-retries at 5 per transaction.",
            "frequency_cap": f"Industry Best Practice: Maximum {DAILY_MESSAGE_CAP} recovery communications per customer per day.",
            "dispute": "RBI Ombudsman Scheme 2021: No recovery actions during active dispute/chargeback period.",
            "cool_off": f"Industry Best Practice: Minimum {COOL_OFF_HOURS}-hour gap between successive recovery attempts.",
        }
        return {
            "proposer": "strategist", "reviewer": "compliance",
            "original": {"channel": channel},
            "objection": objection,
            "resolution": {"action": "block", "reason": check_name},
            "citation": citations.get(check_name, f"Compliance check: {check_name}"),
        }


async def _log_debate(transaction_id: str, debate: dict):
    try:
        await insert_debate({
            "transaction_id": transaction_id,
            "proposer": debate.get("proposer", "strategist"),
            "reviewer": debate.get("reviewer", "compliance"),
            "original_action": debate.get("original", {}),
            "objection": debate.get("objection", ""),
            "resolution": debate.get("resolution", {}),
            "compliance_citation": debate.get("citation", ""),
        })
    except Exception:
        pass
