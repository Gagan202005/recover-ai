"""
RecoverAI — API: Dashboard
Dashboard metrics, agent feed, funnel, patterns endpoints.
"""

from fastapi import APIRouter
from database import supabase, get_dashboard_metrics

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


@router.get("/metrics")
async def dashboard_metrics():
    """Top-level dashboard metrics."""
    return await get_dashboard_metrics()


@router.get("/agent-feed")
async def agent_feed(limit: int = 50):
    """Latest agent actions for the live feed."""
    result = supabase.table("recovery_actions") \
        .select("*, transactions(id, amount, product_name, customer_id)") \
        .order("created_at", desc=True) \
        .limit(limit) \
        .execute()
    return result.data or []


@router.get("/funnel")
async def recovery_funnel():
    """Recovery funnel data for the Sankey diagram."""
    txns = supabase.table("transactions").select("status, recovery_status, failure_reason, amount").neq("status", "success").execute()
    data = txns.data or []

    funnel = {
        "at_risk": {"count": len(data), "amount": sum(t["amount"] for t in data)},
        "detected": {"count": len([t for t in data if t["recovery_status"] != "pending"]), "amount": 0},
        "recovered": {"count": 0, "amount": 0},
        "exception": {"count": 0, "amount": 0},
        "in_progress": {"count": 0, "amount": 0},
    }
    for t in data:
        rs = t["recovery_status"]
        if rs in funnel:
            funnel[rs]["count"] += 1
            funnel[rs]["amount"] += t["amount"]

    return funnel


@router.get("/patterns")
async def failure_patterns():
    """Detected failure patterns — bank outages, failure type clusters, payment method issues, time spikes."""
    txns = supabase.table("transactions").select("bank, failure_reason, error_code, method, status, recovery_status, amount, customer_id, created_at") \
        .neq("status", "success").execute()
    data = txns.data or []

    if not data:
        return []

    patterns = []

    # 1. Bank Outage Detection — ONLY count bank-side infrastructure downtime (declines, timeouts, gateway errors)
    outage_bank_counts = {}
    for t in data:
        reason = t.get("failure_reason")
        source = t.get("error_source")
        # Only true bank downtime errors count as bank outages
        if reason in ("bank_decline", "network_timeout") or source == "gateway" or t.get("is_outage_related"):
            bank = t.get("bank", "unknown")
            outage_bank_counts[bank] = outage_bank_counts.get(bank, 0) + 1

    for bank, count in sorted(outage_bank_counts.items(), key=lambda x: -x[1]):
        if count >= 4:
            patterns.append({
                "type": "bank_outage",
                "icon": "🏦",
                "bank": bank,
                "count": count,
                "description": f"🏦 {bank} Gateway Downtime — {count} infrastructure declines",
                "severity": "high" if count >= 8 else "medium",
            })

    # 2. Failure Type Clusters — group by failure_reason
    reason_counts = {}
    for t in data:
        reason = t.get("failure_reason")
        if reason:
            reason_counts[reason] = reason_counts.get(reason, 0) + 1

    reason_labels = {
        "card_expired": "💳 Expired Cards",
        "insufficient_funds": "💸 Insufficient Funds",
        "bank_decline": "🚫 Bank Declines",
        "network_timeout": "🌐 Network Timeouts",
        "auth_failed": "🔐 Authentication Failures",
        "checkout_abandoned": "🛒 Abandoned Checkouts",
        "mandate_expired": "📋 Expired Mandates",
        "auto_debit_failed": "🔁 Auto-Debit Failures",
        "invoice_overdue": "📄 Overdue Invoices",
    }

    for reason, count in sorted(reason_counts.items(), key=lambda x: -x[1]):
        if count >= 3:
            label = reason_labels.get(reason, reason.replace("_", " ").title())
            patterns.append({
                "type": "failure_cluster",
                "icon": "⚡",
                "failure_reason": reason,
                "count": count,
                "description": f"{label} — {count} occurrences",
                "severity": "high" if count >= 10 else "medium" if count >= 5 else "low",
            })

    # 3. Payment Method Issues — group by method
    method_counts = {}
    for t in data:
        method = t.get("method", "unknown")
        method_counts[method] = method_counts.get(method, 0) + 1

    method_icons = {"card": "💳", "upi": "📱", "netbanking": "🏛️", "wallet": "👛", "emi": "📊"}
    for method, count in sorted(method_counts.items(), key=lambda x: -x[1]):
        if count >= 5:
            icon = method_icons.get(method, "💰")
            patterns.append({
                "type": "method_issue",
                "icon": icon,
                "method": method,
                "count": count,
                "description": f"{icon} {method.upper()} failures — {count} transactions",
                "severity": "medium",
            })

    # 4. High-Value At-Risk — transactions > ₹10,000
    high_value = [t for t in data if t["amount"] >= 1000000 and t.get("recovery_status") in ("pending", "in_progress")]
    if high_value:
        total_amount = sum(t["amount"] for t in high_value) // 100
        patterns.append({
            "type": "high_value_risk",
            "icon": "💰",
            "count": len(high_value),
            "description": f"💰 {len(high_value)} high-value transactions at risk — ₹{total_amount:,}",
            "severity": "high",
        })

    # 5. Recovery Rate by Failure Type
    recovery_stats = {}
    for t in data:
        reason = t.get("failure_reason")
        if reason:
            if reason not in recovery_stats:
                recovery_stats[reason] = {"total": 0, "recovered": 0}
            recovery_stats[reason]["total"] += 1
            if t.get("recovery_status") == "recovered":
                recovery_stats[reason]["recovered"] += 1

    for reason, stats in recovery_stats.items():
        if stats["total"] >= 5:
            rate = round(stats["recovered"] / stats["total"] * 100)
            if rate <= 30:
                label = reason_labels.get(reason, reason.replace("_", " ").title())
                patterns.append({
                    "type": "low_recovery",
                    "icon": "📉",
                    "failure_reason": reason,
                    "count": stats["total"],
                    "recovery_rate": rate,
                    "description": f"📉 Low recovery for {label.split(' ', 1)[-1]} — {rate}% ({stats['recovered']}/{stats['total']})",
                    "severity": "high" if rate <= 15 else "medium",
                })

    return patterns


@router.get("/patterns/detailed")
async def detailed_patterns():
    """Comprehensive multi-dimensional failure patterns for the dedicated Analytics page."""
    txns_res = supabase.table("transactions") \
        .select("*, customers(name, segment, phone, email, city)") \
        .neq("status", "success") \
        .execute()
    data = txns_res.data or []

    if not data:
        return {
            "summary": {"total_failed": 0, "total_at_risk": 0, "outage_banks_count": 0},
            "banks": [],
            "root_causes": [],
            "payment_rails": [],
            "high_value_transactions": [],
        }

    total_at_risk = sum(t.get("amount", 0) for t in data)

    # 1. Banks Breakdown — distinguish between Bank Gateway Outages vs Customer-Side Balance/Card Issues
    bank_map = {}
    for t in data:
        b = t.get("bank") or "Unknown"
        reason = t.get("failure_reason") or ""
        source = t.get("error_source") or ""
        is_bank_error = reason in ("bank_decline", "network_timeout") or source == "gateway" or t.get("is_outage_related", False)

        if b not in bank_map:
            bank_map[b] = {
                "bank": b,
                "count": 0,
                "outage_failures": 0,
                "customer_failures": 0,
                "amount": 0,
                "recovered_count": 0,
                "recovered_amount": 0,
                "error_codes": set(),
                "methods": {},
            }
        bank_map[b]["count"] += 1
        bank_map[b]["amount"] += t.get("amount", 0)
        
        if is_bank_error:
            bank_map[b]["outage_failures"] += 1
        else:
            bank_map[b]["customer_failures"] += 1

        if t.get("recovery_status") == "recovered":
            bank_map[b]["recovered_count"] += 1
            bank_map[b]["recovered_amount"] += (t.get("recovery_amount") or t.get("amount", 0))
        if t.get("error_code"):
            bank_map[b]["error_codes"].add(t["error_code"])
        m = t.get("method") or "other"
        bank_map[b]["methods"][m] = bank_map[b]["methods"].get(m, 0) + 1

    banks_list = []
    for b, d in bank_map.items():
        # Outage is strictly based on bank-side downtime failures, NOT insufficient funds or expired cards
        is_outage = d["outage_failures"] >= 6
        rate = round(d["recovered_count"] / d["count"] * 100, 1) if d["count"] else 0
        
        if is_outage:
            status = "CRITICAL OUTAGE"
            rec_action = f"⚠️ Core banking downtime detected for {b} ({d['outage_failures']} server drops). Auto-retries delayed by 2h; fallback to alternate UPI rails."
        elif d["outage_failures"] >= 3:
            status = "INSTABILITY WARNING"
            rec_action = f"Intermittent gateway degradation on {b}. Retrying with exponential backoff."
        else:
            status = "HEALTHY INFRASTRUCTURE"
            rec_action = f"Bank gateway operational. Failures are customer-side ({d['customer_failures']} balance/auth issues) — immediate WhatsApp/SMS recovery active."

        banks_list.append({
            "bank": b,
            "count": d["count"],
            "outage_failures": d["outage_failures"],
            "customer_failures": d["customer_failures"],
            "amount": d["amount"] // 100,
            "recovered_count": d["recovered_count"],
            "recovered_amount": d["recovered_amount"] // 100,
            "recovery_rate": rate,
            "is_outage": is_outage,
            "status": status,
            "error_codes": list(d["error_codes"]),
            "top_method": max(d["methods"].items(), key=lambda x: x[1])[0] if d["methods"] else "card",
            "recommended_action": rec_action
        })
    banks_list.sort(key=lambda x: (-x["outage_failures"], -x["count"]))

    # 2. Root Causes Breakdown
    reason_labels = {
        "card_expired": {"title": "Expired Credit/Debit Cards", "icon": "💳", "fix": "Automated WhatsApp card update link"},
        "insufficient_funds": {"title": "Insufficient Account Balance", "icon": "💸", "fix": "Smart retry on salary date + partial split payment"},
        "bank_decline": {"title": "Core Bank Declines (Do Not Honor)", "icon": "🚫", "fix": "Outage detection + fallback to UPI QR"},
        "network_timeout": {"title": "Gateway Network Timeouts", "icon": "🌐", "fix": "Instant silent background retry"},
        "auth_failed": {"title": "2FA / OTP Authentication Failed", "icon": "🔐", "fix": "WhatsApp instant 1-click retry payment link"},
        "checkout_abandoned": {"title": "Abandoned Checkout Carts", "icon": "🛒", "fix": "Dynamic 5-10% time-sensitive discount incentive"},
        "mandate_expired": {"title": "Expired Auto-Debit Mandates", "icon": "📋", "fix": "Instant e-Mandate re-authorization flow"},
        "auto_debit_failed": {"title": "Recurring Auto-Debit Failed", "icon": "🔁", "fix": "Fallback to WhatsApp ad-hoc UPI collection"},
        "invoice_overdue": {"title": "B2B Overdue Invoices", "icon": "📄", "fix": "Compliance-gated multi-stage email + WhatsApp follow-up"},
    }

    cause_map = {}
    for t in data:
        r = t.get("failure_reason") or "other"
        if r not in cause_map:
            cause_map[r] = {
                "reason": r,
                "count": 0,
                "amount": 0,
                "recovered_count": 0,
                "recovered_amount": 0,
            }
        cause_map[r]["count"] += 1
        cause_map[r]["amount"] += t.get("amount", 0)
        if t.get("recovery_status") == "recovered":
            cause_map[r]["recovered_count"] += 1
            cause_map[r]["recovered_amount"] += (t.get("recovery_amount") or t.get("amount", 0))

    root_causes_list = []
    for r, d in cause_map.items():
        meta = reason_labels.get(r, {"title": r.replace("_", " ").title(), "icon": "⚡", "fix": "Multi-channel agent recovery"})
        rate = round(d["recovered_count"] / d["count"] * 100, 1) if d["count"] else 0
        root_causes_list.append({
            "reason": r,
            "title": meta["title"],
            "icon": meta["icon"],
            "fix": meta["fix"],
            "count": d["count"],
            "share_percent": round(d["count"] / len(data) * 100, 1),
            "amount": d["amount"] // 100,
            "recovered_count": d["recovered_count"],
            "recovered_amount": d["recovered_amount"] // 100,
            "recovery_rate": rate,
        })
    root_causes_list.sort(key=lambda x: -x["count"])

    # 3. Payment Rails Breakdown
    rail_icons = {"card": "💳 Card", "upi": "📱 UPI", "netbanking": "🏛️ Net Banking", "wallet": "👛 Wallet", "emi": "📊 EMI"}
    rails_map = {}
    for t in data:
        m = t.get("method") or "other"
        if m not in rails_map:
            rails_map[m] = {"method": m, "count": 0, "amount": 0, "recovered_count": 0}
        rails_map[m]["count"] += 1
        rails_map[m]["amount"] += t.get("amount", 0)
        if t.get("recovery_status") == "recovered":
            rails_map[m]["recovered_count"] += 1

    rails_list = []
    for m, d in rails_map.items():
        rate = round(d["recovered_count"] / d["count"] * 100, 1) if d["count"] else 0
        rails_list.append({
            "method": m,
            "label": rail_icons.get(m, m.upper()),
            "count": d["count"],
            "share_percent": round(d["count"] / len(data) * 100, 1),
            "amount": d["amount"] // 100,
            "recovered_count": d["recovered_count"],
            "recovery_rate": rate,
        })
    rails_list.sort(key=lambda x: -x["count"])

    # 4. Top High-Value Transactions At Risk (> ₹10,000)
    high_value_list = []
    for t in sorted(data, key=lambda x: -x.get("amount", 0))[:15]:
        if t.get("amount", 0) >= 1000000:  # >= ₹10,000
            c = t.get("customers") or {}
            high_value_list.append({
                "id": t["id"],
                "amount": t["amount"] // 100,
                "product_name": t.get("product_name", "Order"),
                "bank": t.get("bank", "Unknown"),
                "method": t.get("method", "Unknown"),
                "failure_reason": t.get("failure_reason", "Failed"),
                "recovery_status": t.get("recovery_status", "pending"),
                "customer_name": c.get("name", "Unknown"),
                "customer_segment": c.get("segment", "regular"),
                "customer_city": c.get("city", ""),
                "created_at": t.get("created_at"),
            })

    return {
        "summary": {
            "total_failed": len(data),
            "total_at_risk": total_at_risk // 100,
            "outage_banks_count": len([b for b in banks_list if b["is_outage"]]),
            "top_failure_cause": root_causes_list[0]["title"] if root_causes_list else "None",
            "top_vulnerable_rail": rails_list[0]["label"] if rails_list else "None",
        },
        "banks": banks_list,
        "root_causes": root_causes_list,
        "payment_rails": rails_list,
        "high_value_transactions": high_value_list,
    }


@router.get("/ab-tests")
async def ab_tests():
    """A/B test results."""
    result = supabase.table("ab_tests").select("*").execute()
    return result.data or []


@router.get("/language-stats")
async def language_stats():
    """Recovery performance by language."""
    msgs = supabase.table("channel_messages").select("language, status").execute()
    data = msgs.data or []

    stats = {}
    for m in data:
        lang = m.get("language", "english") or "english"
        if lang not in stats:
            stats[lang] = {"total": 0, "delivered": 0}
        stats[lang]["total"] += 1
        if m.get("status") in ("sent", "delivered"):
            stats[lang]["delivered"] += 1

    return stats
