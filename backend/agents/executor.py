"""
RecoverAI — Agent 5: EXECUTOR
Action agent — calls MCP tools to execute recovery actions.
For batch processing, calls channel wrappers directly (MCP for live demos).
"""

import time
import random
from datetime import datetime
from agents.state import RecoveryState
from database import insert_recovery_action, insert_channel_message, update_transaction
from channels.razorpay_client import create_payment_link
from channels.twilio_client import make_voice_call, build_hinglish_twiml
from channels.sms_router import dispatch_sms, dispatch_whatsapp
from channels.email_client import send_email, build_recovery_email_html
from channels.message_templates import render_template, select_language
from config import settings

# Recovery probabilities per channel
RECOVERY_PROBS = {
    "network_timeout": {"auto_retry": 0.90, "whatsapp": 0.60, "sms": 0.45, "email": 0.35},
    "bank_outage": {"auto_retry": 0.78, "whatsapp": 0.45, "sms": 0.30, "email": 0.25},
    "bank_decline": {"auto_retry": 0.65, "whatsapp": 0.45, "sms": 0.30, "email": 0.25},
    "insufficient_funds": {"whatsapp": 0.38, "sms": 0.25, "email": 0.20, "voice": 0.30},
    "card_expired": {"whatsapp": 0.40, "sms": 0.25, "email": 0.20, "voice": 0.45},
    "auth_failed": {"whatsapp": 0.35, "sms": 0.22, "email": 0.15},
    "checkout_abandoned": {"whatsapp": 0.30, "sms": 0.18, "email": 0.15},
    "mandate_expired": {"whatsapp": 0.35, "sms": 0.25, "email": 0.30},
    "auto_debit_failed": {"auto_retry": 0.60, "whatsapp": 0.35, "sms": 0.20},
    "invoice_overdue": {"email": 0.55, "whatsapp": 0.40, "voice": 0.60},
}


async def executor_node(state: RecoveryState) -> dict:
    """Executor agent: execute recovery action via real channels or simulate outcome for batch."""
    start_time = time.time()

    compliance = state.get("compliance_result", {})
    strategy = state.get("strategy", {})
    diagnosis = state.get("diagnosis", {})
    is_live = state.get("is_live_demo", False)

    # If compliance blocked, skip execution
    if compliance.get("verdict") == "blocked":
        block_reason = compliance.get("block_reason", "")
        if not block_reason:
            # Build reason from failed checks
            failed = compliance.get("checks_failed", [])
            mods = compliance.get("modifications", [])
            reasons = [m.get("reason", "") for m in mods] + failed
            block_reason = f"Compliance blocked: {', '.join(reasons)}" if reasons else "Compliance blocked"
        result = {"channel": "none", "outcome": "blocked", "reason": block_reason,
                  "checks_failed": compliance.get("checks_failed", [])}
        duration_ms = int((time.time() - start_time) * 1000)
        await insert_recovery_action({
            "transaction_id": state["transaction_id"], "agent": "executor",
            "action": "skipped", "details": result, "result": "blocked", "duration_ms": duration_ms,
        })
        return {"execution_result": result,
                "audit_trail": state.get("audit_trail", []) + [{"agent": "executor", "action": "skipped", "ts": datetime.utcnow().isoformat()}]}

    # Note: human_review verdict no longer exists (we only send payment links, not auto-debit)
    # All non-blocked transactions proceed to execution.


    # If compliance modified with scheduling delays, log but don't send now (unless live demo)
    if compliance.get("verdict") == "modified":
        mods = compliance.get("modifications", [])
        blocking_mods = [m for m in mods if m.get("revised", "").startswith(("schedule_", "wait_"))]
        if blocking_mods and not is_live:
            mod_detail = blocking_mods[0]
            result = {"channel": strategy.get("channel", "whatsapp"), "outcome": "scheduled",
                      "reason": f"Compliance modified: {mod_detail.get('reason', 'scheduling required')}",
                      "scheduled_action": mod_detail.get("revised", "schedule_tomorrow")}
            duration_ms = int((time.time() - start_time) * 1000)
            await insert_recovery_action({
                "transaction_id": state["transaction_id"], "agent": "executor",
                "action": "scheduled", "details": result, "result": "scheduled", "duration_ms": duration_ms,
            })
            return {"execution_result": result,
                    "audit_trail": state.get("audit_trail", []) + [{"agent": "executor", "action": "scheduled", "ts": datetime.utcnow().isoformat()}]}

    channel = strategy.get("channel", "whatsapp")
    language = strategy.get("language", "english")
    root_cause = diagnosis.get("root_cause", "unknown")
    amount_display = f"{state['amount'] // 100:,}"

    # Create payment link (REAL Razorpay API)
    payment_link_url = ""
    try:
        link = create_payment_link(
            amount=state["amount"], customer_name=state.get("customer_name", "Customer"),
            customer_email=state.get("customer_email", ""), customer_phone=state.get("customer_phone", ""),
            description=f"Complete your purchase - {state.get('product_name', 'Order')}",
        )
        payment_link_url = link.get("short_url", "https://rzp.io/i/demo")
    except Exception:
        payment_link_url = "https://rzp.io/i/demo"

    # Execute channel action
    message_content = ""
    external_id = ""
    channel_status = "sent"

    if is_live:
        # LIVE DEMO: Real API calls
        result = await _execute_live(channel, state, language, payment_link_url, amount_display)
        message_content = result.get("message_content", "")
        external_id = result.get("external_id", "")
    else:
        # BATCH: Generate message but simulate delivery outcome
        message_content = render_template(
            f"recovery_{channel}" if channel in ("whatsapp", "sms") else "recovery_whatsapp",
            language, name=state.get("customer_name", "Customer"),
            amount=amount_display, product=state.get("product_name", "Order"),
            link=payment_link_url,
        )
        external_id = f"sim_{channel}_{state['transaction_id']}"

    # Determine outcome (probability-based for batch, real for live)
    probs = RECOVERY_PROBS.get(root_cause, {})
    recovery_prob = probs.get(channel, 0.3)
    recovered = random.random() < recovery_prob if not is_live else False  # Live waits for real payment

    outcome = "recovered" if recovered else ("pending" if is_live else "attempted")

    # Log channel message
    await insert_channel_message({
        "transaction_id": state["transaction_id"],
        "customer_id": state["customer_id"],
        "channel": channel, "language": language,
        "message_content": message_content[:500],
        "external_id": external_id,
        "payment_link_url": payment_link_url,
        "status": channel_status,
    })

    # Update transaction
    update_data = {"recovery_status": "recovered" if recovered else "in_progress",
                   "attempt_count": (state.get("attempt_count", 0) or 0) + 1}
    if recovered:
        update_data["recovery_amount"] = state["amount"]
        update_data["recovered_at"] = datetime.utcnow().isoformat()
    await update_transaction(state["transaction_id"], update_data)

    execution_result = {
        "channel": channel, "language": language,
        "message_content": message_content[:200],
        "external_id": external_id,
        "payment_link_url": payment_link_url,
        "outcome": outcome, "recovered": recovered,
        "mcp_server": "comms-recovery" if channel in ("whatsapp", "sms", "email", "voice") else "razorpay-recovery",
        "mcp_tool": f"tool_send_{channel}" if channel in ("whatsapp", "sms", "email") else "tool_create_payment_link",
    }

    duration_ms = int((time.time() - start_time) * 1000)

    await insert_recovery_action({
        "transaction_id": state["transaction_id"], "agent": "executor",
        "action": "executed", "details": execution_result,
        "result": outcome, "duration_ms": duration_ms,
    })

    return {
        "execution_result": execution_result,
        "status": "recovered" if recovered else state.get("status", "processing"),
        "audit_trail": state.get("audit_trail", []) + [{"agent": "executor", "action": "executed", "ts": datetime.utcnow().isoformat()}],
    }


async def _execute_live(channel: str, state: dict, language: str, payment_link_url: str, amount_display: str) -> dict:
    """Execute real API calls for live demo scenarios."""
    phone = state.get("customer_phone", settings.demo_phone_number)
    email = state.get("customer_email", settings.demo_email)
    name = state.get("customer_name", settings.demo_customer_name)
    product = state.get("product_name", "Order")
    dynamic_incentive = state.get("strategy", {}).get("dynamic_incentive")

    if channel == "whatsapp":
        msg = render_template("recovery_whatsapp", language, name=name, amount=amount_display, product=product, link=payment_link_url)
        if dynamic_incentive:
            # Insert dynamic offer before opt out notice
            msg = msg.replace("Reply STOP to opt out.", f"🎁 Special Offer: {dynamic_incentive}\nReply STOP to opt out.")
        result = dispatch_whatsapp(phone, msg)
        return {"message_content": msg, "external_id": result.get("message_sid", "")}

    elif channel == "sms":
        msg = render_template("recovery_sms", language, name=name, amount=amount_display, product=product, link=payment_link_url)
        if dynamic_incentive:
            msg = f"{msg} Offer: {dynamic_incentive}"
        result = dispatch_sms(phone, msg)
        return {"message_content": msg, "external_id": result.get("message_sid", "")}

    elif channel == "email":
        subject = render_template("recovery_email_subject", language, amount=amount_display)
        html = build_recovery_email_html(name, f"₹{amount_display}", product, payment_link_url, settings.merchant_name)
        result = send_email(email, subject, html)
        return {"message_content": f"Email: {subject}", "external_id": result.get("message_id", "")}

    elif channel == "voice":
        voice_script = state.get("strategy", {}).get("voice_script")
        if not voice_script:
            voice_script = build_hinglish_twiml(name, int(amount_display.replace(",", "")), product)
        result = make_voice_call(phone, voice_script)
        return {"message_content": f"AI Voice Call: {voice_script}", "external_id": result.get("call_sid", "")}

    elif channel == "auto_retry":
        # Auto-retry: create a fresh payment link and send context-specific WhatsApp message
        bank_name = state.get("bank", "Bank")
        is_outage = state.get("diagnosis", {}).get("is_outage", False)
        root_cause = state.get("diagnosis", {}).get("root_cause", "bank_decline")

        if is_outage or root_cause == "bank_outage":
            # Bank outage — notify about scheduled retry + send alternate link
            msg = render_template("recovery_whatsapp", language, name=name, amount=amount_display, product=product, link=payment_link_url)
            msg = f"⚠️ {bank_name} is experiencing temporary downtime. We've scheduled an auto-retry in 2 hours.\n\nMeanwhile, you can complete your payment using this alternate link:\n{payment_link_url}\n\n" + msg
        elif root_cause == "network_timeout":
            # Network timeout — instant silent retry message
            msg = f"Hi {name}! 👋\n\nYour payment of ₹{amount_display} for {product} timed out due to a network issue. We've re-initiated it for you.\n\n⚡ Tap to complete instantly:\n{payment_link_url}\n\nThis link expires in 24h."
        else:
            # Bank decline — fresh payment link with retry framing
            msg = f"Hi {name}! 👋\n\nYour payment of ₹{amount_display} for {product} didn't go through this time. No worries — we've generated a fresh payment link for you.\n\n⚡ Tap to retry instantly:\n{payment_link_url}\n\n💡 Tip: You can also try UPI or Net Banking if your card isn't working.\n\nThis link expires in 24h."

        result = dispatch_whatsapp(phone, msg)
        return {"message_content": f"Auto-retry ({root_cause}): {msg[:150]}", "external_id": result.get("message_sid", "")}

    elif channel == "payment_link":
        # Just send the payment link via WhatsApp
        msg = render_template("recovery_whatsapp", language, name=name, amount=amount_display, product=product, link=payment_link_url)
        result = dispatch_whatsapp(phone, msg)
        return {"message_content": msg, "external_id": result.get("message_sid", "")}

    return {"message_content": "", "external_id": ""}
