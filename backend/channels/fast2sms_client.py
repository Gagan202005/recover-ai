"""
RecoverAI — Channel: Fast2SMS Client
Sends custom SMS directly to Indian phone numbers without DLT/template restrictions.
"""

import os
import sys
import requests
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import settings


def send_fast2sms(to_phone: str, message: str) -> dict:
    """Send direct custom SMS using Fast2SMS Quick SMS route (no DLT required)."""
    api_key = os.getenv("FAST2SMS_API_KEY", settings.fast2sms_api_key)
    
    phone = to_phone.replace("+91", "").replace("+", "").strip()
    if len(phone) > 10:
        phone = phone[-10:]

    url = "https://www.fast2sms.com/dev/bulkV2"
    headers = {
        "authorization": api_key,
        "accept": "application/json",
    }
    
    # Try Quick SMS route (route 'q') - supports custom text with links
    payload = {
        "route": "q",
        "message": message,
        "language": "english",
        "flash": 0,
        "numbers": phone,
    }

    try:
        resp = requests.post(url, headers=headers, data=payload, timeout=10)
        data = resp.json()

        if data.get("return"):
            return {
                "message_sid": f"f2s_{data.get('request_id', phone)}",
                "status": "sent",
                "channel": "sms",
                "provider": "fast2sms",
                "message_content": message,
            }
        else:
            return {
                "message_sid": f"f2s_err_{phone}",
                "status": "error",
                "channel": "sms",
                "provider": "fast2sms",
                "note": data.get("message", "Fast2SMS error"),
                "message_content": message,
            }
    except Exception as e:
        return {
            "message_sid": f"f2s_fail_{phone}",
            "status": "failed",
            "channel": "sms",
            "provider": "fast2sms",
            "note": str(e),
            "message_content": message,
        }
