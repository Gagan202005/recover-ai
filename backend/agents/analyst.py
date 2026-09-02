"""
RecoverAI — Agent 6: ANALYST
Intelligent Learning & Reporting — uses Gemini AI for pattern detection,
updates metrics, RAG playbook, A/B tests, and generates actionable insights.
"""

import time
import json
import re
from datetime import datetime
from agents.state import RecoveryState
from database import insert_recovery_action, supabase
from rag.embeddings import get_embedding
from rag.pinecone_client import upsert_documents
import google.generativeai as genai
from config import settings

genai.configure(api_key=settings.google_api_key)
model = genai.GenerativeModel(settings.gemini_model)


async def analyst_node(state: RecoveryState) -> dict:
    """Analyst agent: learn from outcome, update playbook, detect patterns using Gemini AI."""
    start_time = time.time()

    execution = state.get("execution_result", {})
    diagnosis = state.get("diagnosis", {})
    strategy = state.get("strategy", {})
    compliance = state.get("compliance_result", {})
    recovered = execution.get("recovered", False)
    channel = execution.get("channel", "unknown")
    root_cause = diagnosis.get("root_cause", "unknown")

    # 1. Update A/B test if active
    ab_experiment = strategy.get("ab_experiment")
    if ab_experiment:
        try:
            test_id = ab_experiment["test_id"]
            variant = ab_experiment["variant"]
            test = supabase.table("ab_tests").select("*").eq("id", test_id).single().execute()
            if test.data:
                t = test.data
                if variant == t["variant_a"]:
                    updates = {"variant_a_trials": t["variant_a_trials"] + 1}
                    if recovered:
                        updates["variant_a_successes"] = t["variant_a_successes"] + 1
                else:
                    updates = {"variant_b_trials": t["variant_b_trials"] + 1}
                    if recovered:
                        updates["variant_b_successes"] = t["variant_b_successes"] + 1

                # Check for statistical significance (simplified: >30 trials + >10% difference)
                total_a = t.get("variant_a_trials", 0) + (1 if variant == t["variant_a"] else 0)
                total_b = t.get("variant_b_trials", 0) + (1 if variant != t["variant_a"] else 0)
                if total_a >= 15 and total_b >= 15:
                    rate_a = (t.get("variant_a_successes", 0) + (1 if variant == t["variant_a"] and recovered else 0)) / max(total_a, 1)
                    rate_b = (t.get("variant_b_successes", 0) + (1 if variant != t["variant_a"] and recovered else 0)) / max(total_b, 1)
                    if abs(rate_a - rate_b) > 0.10:
                        updates["is_significant"] = True
                        winner = t["variant_a"] if rate_a > rate_b else t["variant_b"]
                        updates["winner"] = winner

                supabase.table("ab_tests").update(updates).eq("id", test_id).execute()
        except Exception:
            pass

    # 2. Add case to RAG playbook — learn from BOTH successes AND failures
    # Failed strategies help the strategist avoid repeating bad approaches
    try:
        outcome_label = "successful" if recovered else "failed"
        case_text = (
            f"Recovery Case ({outcome_label}): {root_cause} failure for ₹{state['amount'] // 100}. "
            f"Customer segment: {state.get('customer_context', {}).get('segment', 'regular')}. "
            f"Bank: {state.get('bank', 'unknown')}. Method: {state.get('method', 'unknown')}. "
            f"Strategy: {channel}. Language: {strategy.get('language', 'english')}. "
            f"Tone: {strategy.get('tone', 'friendly')}. "
            f"Dynamic incentive: {strategy.get('dynamic_incentive', 'none')}. "
            f"Recovery {outcome_label}."
        )
        embedding = await get_embedding(case_text)
        upsert_documents([{
            "id": f"case_{state['transaction_id']}",
            "values": embedding,
            "metadata": {
                "content": case_text,
                "failure_type": root_cause,
                "channel_used": channel,
                "language": strategy.get("language", "english"),
                "outcome": "success" if recovered else "failure",
                "amount": state["amount"],
                "customer_segment": state.get("customer_context", {}).get("segment", "regular"),
                "bank": state.get("bank", "unknown"),
                "method": state.get("method", "unknown"),
            },
        }], namespace="recovery_playbook")
    except Exception:
        pass

    # 3. Detect patterns using Gemini AI
    patterns = []

    # Bank outage pattern (from diagnosis)
    if diagnosis.get("is_outage"):
        bank = state.get("bank", "unknown")
        correlated = diagnosis.get("correlated_transactions", [])
        patterns.append({
            "type": "bank_outage",
            "bank": bank,
            "correlated_count": len(correlated),
            "description": f"{bank} outage detected — {len(correlated)} correlated failures",
        })

    # Use Gemini for deeper pattern analysis
    gemini_insights = ""
    try:
        prompt = f"""You are a payment recovery analyst. Analyze this recovery case and provide actionable insights.

CASE DATA:
- Root Cause: {root_cause}
- Channel Used: {channel}
- Recovery Outcome: {"SUCCESS ✅" if recovered else "FAILED ❌"}
- Amount: ₹{state['amount'] // 100}
- Bank: {state.get('bank', 'unknown')}
- Payment Method: {state.get('method', 'unknown')}
- Customer Segment: {state.get('customer_context', {}).get('segment', 'regular')}
- Language Used: {strategy.get('language', 'english')}
- Tone Used: {strategy.get('tone', 'friendly')}
- Dynamic Incentive: {strategy.get('dynamic_incentive', 'none')}
- Gemini Strategy Reasoning: {strategy.get('gemini_reasoning', 'N/A')}
- Compliance Verdict: {compliance.get('verdict', 'N/A')}
- Compliance Checks Failed: {compliance.get('checks_failed', [])}
- Is Bank Outage: {diagnosis.get('is_outage', False)}
- A/B Test Active: {ab_experiment is not None}

Provide a JSON response:
{{
  "insight": "1-2 sentence key takeaway from this case",
  "recommendation": "what to do differently next time for similar cases",
  "pattern_type": "one of: channel_optimization|timing_insight|segment_behavior|bank_pattern|incentive_effectiveness|language_impact|none",
  "confidence": 0.0-1.0
}}

Respond ONLY with valid JSON. No markdown."""

        import asyncio
        response = await asyncio.to_thread(model.generate_content, prompt)
        raw = response.text.strip()
        raw = re.sub(r"^```json\s*", "", raw)
        raw = re.sub(r"^```\s*", "", raw)
        raw = re.sub(r"\s*```$", "", raw)
        gemini_analysis = json.loads(raw)

        gemini_insights = gemini_analysis.get("insight", "")

        if gemini_analysis.get("pattern_type", "none") != "none":
            patterns.append({
                "type": gemini_analysis["pattern_type"],
                "description": gemini_analysis.get("insight", ""),
                "recommendation": gemini_analysis.get("recommendation", ""),
                "confidence": gemini_analysis.get("confidence", 0.5),
            })

    except Exception as e:
        gemini_insights = f"Analysis fallback: {channel} {'succeeded' if recovered else 'failed'} for {root_cause}"

    analysis = {
        "recovery_successful": recovered,
        "amount_recovered": state["amount"] if recovered else 0,
        "channel_used": channel,
        "root_cause": root_cause,
        "strategy_reinforced": f"{channel} for {root_cause}" if recovered else None,
        "ab_test_updated": ab_experiment is not None,
        "playbook_updated": recovered,
        "patterns_detected": patterns,
        "gemini_insight": gemini_insights,
    }

    duration_ms = int((time.time() - start_time) * 1000)

    await insert_recovery_action({
        "transaction_id": state["transaction_id"], "agent": "analyst",
        "action": "analyzed", "details": analysis,
        "result": "success", "duration_ms": duration_ms,
    })

    final_status = "recovered" if recovered else state.get("status", "processing")
    if execution.get("outcome") == "blocked" or compliance.get("verdict") == "blocked":
        final_status = "exception"
    elif execution.get("outcome") == "human_review" or compliance.get("verdict") == "human_review":
        final_status = "human_review"

    # Ensure transaction status in DB is updated for blocked/human_review/exceptions
    if final_status in ("exception", "human_review"):
        try:
            supabase.table("transactions").update({"recovery_status": final_status}).eq("id", state["transaction_id"]).execute()
        except Exception:
            pass

    return {
        "analysis": analysis,
        "status": final_status,
        "audit_trail": state.get("audit_trail", []) + [{"agent": "analyst", "action": "analyzed", "ts": datetime.utcnow().isoformat()}],
    }


async def trigger_post_recovery_analysis(txn_id: str, amount: int = None, payment_id: str = "") -> dict:
    """Run Agent 6 (Analyst) when a payment is marked recovered in DB.
    Updates RAG playbook, A/B test statistics, and generates post-recovery insights."""
    print(f"🧠 [Analyst Post-Recovery] Triggered for recovered transaction: {txn_id}")
    try:
        # 1. Fetch transaction
        res = supabase.table("transactions").select("*").eq("id", txn_id).execute()
        if not res.data:
            print(f"⚠️ [Analyst] Transaction {txn_id} not found in DB")
            return {}
        txn = res.data[0]

        # 2. Fetch customer
        cust_res = supabase.table("customers").select("*").eq("id", txn.get("customer_id", "cust_001")).execute()
        customer = cust_res.data[0] if cust_res.data else {}

        # 3. Fetch past actions for this transaction
        actions_res = supabase.table("recovery_actions").select("*").eq("transaction_id", txn_id).order("created_at").execute()
        actions = actions_res.data or []

        diagnosis = {}
        strategy = {}
        compliance = {}
        execution = {}

        for act in actions:
            ag = act.get("agent")
            det = act.get("details") or {}
            if ag == "diagnostician":
                diagnosis = det
            elif ag == "strategist":
                strategy = det
            elif ag == "compliance":
                compliance = det
            elif ag == "executor":
                execution = det

        # Default fallback values if actions were sparse
        root_cause = txn.get("failure_reason") or diagnosis.get("root_cause") or "bank_decline"
        if not diagnosis:
            diagnosis = {"root_cause": root_cause, "confidence": 0.85, "explanation": txn.get("error_description", "Payment recovery successful")}

        channel = execution.get("channel") or strategy.get("channel") or "whatsapp"
        if not strategy:
            strategy = {"channel": channel, "language": "hinglish", "tone": "warm_friendly"}

        recovered_amount = amount or txn.get("recovery_amount") or txn.get("amount", 0)

        # Build recovered execution state
        execution_result = {
            "channel": channel,
            "outcome": "recovered",
            "recovered": True,
            "amount": recovered_amount,
            "payment_id": payment_id or txn.get("razorpay_payment_id", ""),
            "external_id": execution.get("external_id", ""),
            "message_content": execution.get("message_content", "Payment completed successfully by customer."),
        }

        state: RecoveryState = {
            "transaction_id": txn_id,
            "razorpay_order_id": txn.get("razorpay_order_id", ""),
            "amount": recovered_amount,
            "currency": txn.get("currency", "INR"),
            "customer_id": txn.get("customer_id", "cust_001"),
            "customer_name": customer.get("name", "Customer"),
            "customer_phone": customer.get("phone", ""),
            "customer_email": customer.get("email", ""),
            "product_name": txn.get("product_name", "Product"),
            "failure_reason": root_cause,
            "error_code": txn.get("error_code", "SUCCESS"),
            "error_description": txn.get("error_description", ""),
            "error_source": txn.get("error_source", ""),
            "bank": txn.get("bank", "Bank"),
            "method": txn.get("method", "card"),
            "is_live_demo": True,
            "diagnosis": diagnosis,
            "strategy": strategy,
            "compliance_result": compliance,
            "execution_result": execution_result,
            "customer_context": customer,
            "status": "recovered",
        }

        # Run analyst node
        result = await analyst_node(state)
        print(f"✅ [Analyst Post-Recovery] Learning completed! Playbook & metrics updated for {txn_id}")
        return result
    except Exception as e:
        print(f"⚠️ [Analyst Post-Recovery] Error running analyst: {e}")
        return {}
