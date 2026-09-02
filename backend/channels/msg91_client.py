"""
RecoverAI — Channel: MSG91 Client
SMS and WhatsApp via MSG91 (India's #1 CPaaS).
Replaces Twilio for Indian phone numbers with full custom text support.
"""

import requests
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import settings


MSG91_AUTH_KEY = os.getenv("MSG91_AUTH_KEY", "")
MSG91_SENDER = "RCVRAI"  # 6-char sender ID


def send_sms(to_phone: str, message: str) -> dict:
    """Send an SMS via MSG91 with full custom text to Indian numbers."""
    # Strip country code prefix formats
    phone = to_phone.replace("+91", "").replace("+", "").strip()
    if not phone.startswith("91"):
        phone = f"91{phone}"

    headers = {
        "authkey": MSG91_AUTH_KEY,
        "content-type": "application/json",
    }

    payload = {
        "sender": MSG91_SENDER,
        "route": "1",  # transactional
        "country": "91",
        "sms": [
            {
                "message": message,
                "to": [phone],
            }
        ],
    }

    try:
        resp = requests.post(
            "https://api.msg91.com/api/v2/sendsms",
            json=payload,
            headers=headers,
            timeout=10,
        )
        data = resp.json() if resp.headers.get("content-type", "").startswith("application/json") else {"raw": resp.text}

        if resp.status_code == 200 and data.get("type") == "success":
            return {
                "message_sid": data.get("message", resp.text[:30]),
                "status": "queued",
                "channel": "sms",
                "provider": "msg91",
            }
        else:
            return {
                "message_sid": f"msg91_err_{phone[-6:]}",
                "status": "error",
                "channel": "sms",
                "provider": "msg91",
                "note": f"MSG91 error: {str(data)[:150]}",
                "message_content": message,
            }
    except Exception as e:
        return {
            "message_sid": f"msg91_fail_{phone[-6:]}",
            "status": "failed",
            "channel": "sms",
            "provider": "msg91",
            "note": f"MSG91 exception: {str(e)[:150]}",
            "message_content": message,
        }
