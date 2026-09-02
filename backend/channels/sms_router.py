"""
RecoverAI — Channel: Smart SMS & WhatsApp Router
Dispatches messages through the best available provider with automatic fallback:
Fast2SMS -> MSG91 -> Twilio -> Resend Email.
"""

from channels.wabery_client import send_whatsapp as send_wabery_whatsapp
from channels.fast2sms_client import send_fast2sms
from channels.msg91_client import send_sms as send_msg91_sms
from channels.twilio_client import send_sms as send_twilio_sms


def dispatch_sms(to_phone: str, message: str) -> dict:
    """Smart SMS dispatcher with automatic fallback chain."""
    # 1. Try Fast2SMS first
    res = send_fast2sms(to_phone, message)
    if res.get("status") in ("sent", "queued"):
        return res

    # 2. Try MSG91
    res = send_msg91_sms(to_phone, message)
    if res.get("status") in ("sent", "queued"):
        return res

    # 3. Fall back to Twilio SMS (template)
    res = send_twilio_sms(to_phone, message)
    return res


def dispatch_whatsapp(to_phone: str, message: str) -> dict:
    """Dedicated WhatsApp dispatcher using Wabery (live custom two-way messaging)."""
    return send_wabery_whatsapp(to_phone, message)

