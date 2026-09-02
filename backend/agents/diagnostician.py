"""
RecoverAI — Agent 2: DIAGNOSTICIAN
Root Cause Analysis using RAG + failure correlation.
"""

import time
import json
from datetime import datetime
from agents.state import RecoveryState
from database import insert_recovery_action, get_recent_failures_by_bank
from rag.pinecone_client import query_error_codes
import google.generativeai as genai
from config import settings

genai.configure(api_key=settings.google_api_key)
model = genai.GenerativeModel(settings.gemini_model)


async def diagnostician_node(state: RecoveryState) -> dict:
    """Diagnostician agent: diagnose root cause with RAG evidence."""
    start_time = time.time()

    error_code = state.get("error_code", "unknown")
    bank = state.get("bank", "unknown")
    failure_reason = state.get("failure_reason", "unknown")

    # 1. RAG query — error codes knowledge base
    rag_results = []
    rag_citations = []
    try:
        rag_results = await query_error_codes(error_code, bank)
        rag_citations = [{"source": "KB1:error_codes", "content": r["content"][:200], "score": r["score"]} for r in rag_results[:3]]
    except Exception as e:
        rag_citations = [{"source": "KB1:error_codes", "error": str(e)}]

    # 2. Correlation check — only correlate genuine bank gateway / downtime errors (ignoring customer balance/card issues)
    correlated_txns = []
    is_outage = False
    try:
        recent = await get_recent_failures_by_bank(bank, minutes=30)
        outage_drops = [
            t["id"] for t in (recent or [])
            if t["id"] != state["transaction_id"] and (
                t.get("failure_reason") in ("bank_decline", "network_timeout")
                or t.get("error_source") == "gateway"
                or t.get("is_outage_related")
            )
        ]
        correlated_txns = outage_drops
        is_outage = len(correlated_txns) >= 4
    except Exception:
        pass

    # 3. LLM diagnosis
    rag_context = "\n".join([r["content"] for r in rag_results[:3]]) if rag_results else "No RAG data available."
    
    prompt = f"""You are a payment failure diagnostician. Analyze this failure and provide a root cause.

FAILURE DATA:
- Error code: {error_code}
- Bank: {bank}
- Failure reason: {failure_reason}
- Error description: {state.get('error_description', 'N/A')}
- Error source: {state.get('error_source', 'N/A')}
- Payment method: {state.get('method', 'N/A')}
- Amount: ₹{state['amount'] // 100}
- Correlated failures from same bank (last 30 min): {len(correlated_txns)}
- Is likely outage: {is_outage}

KNOWLEDGE BASE CONTEXT:
{rag_context}

Respond in JSON format:
{{"root_cause": "string (bank_outage|insufficient_funds|card_expired|network_timeout|auth_failed|mandate_expired|auto_debit_failed|checkout_abandoned|invoice_overdue|unknown)",
 "confidence": 0.0-1.0,
 "evidence": ["list of evidence strings"],
 "explanation": "one-line human-readable explanation"}}"""

    try:
        import asyncio
        response = await asyncio.to_thread(model.generate_content, prompt)
        text = response.text.strip()
        if text.startswith("```"):
            text = text.split("\n", 1)[1].rsplit("```", 1)[0].strip()
        diagnosis_llm = json.loads(text)
    except Exception:
        diagnosis_llm = {
            "root_cause": failure_reason or "unknown",
            "confidence": 0.6,
            "evidence": [f"Error code: {error_code}", f"Bank: {bank}"],
            "explanation": f"Payment failed with code {error_code} from {bank}",
        }

    # Guard: if Gemini disagrees with the transaction's known failure_reason AND
    # its confidence is low (<0.7), prefer the original — prevents LLM misclassification
    # from derailing the strategist/executor pipeline
    llm_root_cause = diagnosis_llm.get("root_cause", "unknown")
    llm_confidence = diagnosis_llm.get("confidence", 0.5)
    valid_reasons = {"bank_decline", "card_expired", "insufficient_funds", "network_timeout",
                     "auth_failed", "checkout_abandoned", "mandate_expired", "auto_debit_failed",
                     "invoice_overdue", "bank_outage"}

    if (failure_reason in valid_reasons
            and llm_root_cause != failure_reason
            and llm_confidence < 0.7):
        diagnosis_llm["evidence"] = diagnosis_llm.get("evidence", []) + [
            f"LLM suggested '{llm_root_cause}' (confidence {llm_confidence}) but transaction has '{failure_reason}' — using transaction value"
        ]
        diagnosis_llm["root_cause"] = failure_reason

    # Override with outage if detected
    if is_outage:
        diagnosis_llm["root_cause"] = "bank_outage"
        diagnosis_llm["confidence"] = max(diagnosis_llm.get("confidence", 0), 0.85)
        diagnosis_llm["evidence"].append(f"{len(correlated_txns)} correlated {bank} failures in 30 min")

    diagnosis = {
        **diagnosis_llm,
        "is_outage": is_outage,
        "correlated_transactions": correlated_txns[:10],
        "rag_citations": rag_citations,
    }

    duration_ms = int((time.time() - start_time) * 1000)

    await insert_recovery_action({
        "transaction_id": state["transaction_id"],
        "agent": "diagnostician",
        "action": "diagnosed",
        "details": {k: v for k, v in diagnosis.items() if k != "rag_citations"},
        "rag_citations": rag_citations,
        "result": "success",
        "duration_ms": duration_ms,
    })

    return {
        "diagnosis": diagnosis,
        "audit_trail": state.get("audit_trail", []) + [{"agent": "diagnostician", "action": "diagnosed", "ts": datetime.utcnow().isoformat()}],
    }
