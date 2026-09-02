"""
RecoverAI — Channel: Wabery Client
Live Two-Way WhatsApp Messaging via Wabery Sandbox / Cloud API.
Supports real outbound payment recovery messages & reply routing.
"""

import os
import sys
import requests

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import settings


WABERY_API_KEY = os.getenv("WABERY_API_KEY", settings.wabery_api_key)
WABERY_CHANNEL_ID = os.getenv("WABERY_CHANNEL_ID", settings.wabery_channel_id)
WABERY_CONVERSATION_ID = os.getenv("WABERY_CONVERSATION_ID", settings.wabery_conversation_id)


def send_whatsapp(to_phone: str, message: str, conv_id: str = None, chan_id: str = None) -> dict:
    """Send a custom WhatsApp message to customer via Wabery."""
    headers = {
        "Authorization": f"Bearer {WABERY_API_KEY}",
        "Content-Type": "application/json",
    }

    # Use explicitly passed IDs or fallback to environment / active conversation
    conv_id = conv_id or WABERY_CONVERSATION_ID
    chan_id = chan_id or WABERY_CHANNEL_ID

    try:
        if not conv_id or not chan_id:
            r = requests.get("https://api.wabery.com/v1/conversations", headers=headers, timeout=5)
            data = r.json().get("data", [])
            if data:
                conv_id = data[0]["id"]
                chan_id = data[0].get("last_channel_id") or data[0].get("channel_id")

        payload = {
            "channel_id": chan_id,
            "conversation_id": conv_id,
            "text": message,
        }

        print(f"📤 [Wabery Send] Sending to conv={conv_id}, chan={chan_id}, msg_len={len(message)}")
        resp = requests.post("https://api.wabery.com/v1/messages", headers=headers, json=payload, timeout=10)
        
        # If conversation/channel ID expired or invalid, auto-refresh from /conversations
        if resp.status_code in (400, 404, 422):
            try:
                r_fresh = requests.get("https://api.wabery.com/v1/conversations", headers=headers, timeout=5)
                convs = r_fresh.json().get("data", [])
                if convs:
                    conv_id = convs[0]["id"]
                    chan_id = convs[0].get("last_channel_id") or convs[0].get("channel_id")
                    payload["conversation_id"] = conv_id
                    payload["channel_id"] = chan_id
                    print(f"🔄 [Wabery Send] Auto-refreshed: conv={conv_id}, chan={chan_id}. Retrying send...")
                    resp = requests.post("https://api.wabery.com/v1/messages", headers=headers, json=payload, timeout=10)
            except Exception as ref_err:
                print(f"⚠️ [Wabery Send] Refresh error: {ref_err}")

        print(f"📤 [Wabery Send] Response status={resp.status_code}, body={resp.text[:300]}")
        data = resp.json()

        if resp.status_code in (200, 201, 202):
            return {
                "message_sid": data.get("id", "wab_sent"),
                "status": "queued",
                "channel": "whatsapp",
                "provider": "wabery",
                "message_content": message,
            }
        else:
            print(f"❌ [Wabery Send] ERROR: status={resp.status_code}, response={resp.text[:500]}")
            return {
                "message_sid": "wab_err",
                "status": "error",
                "channel": "whatsapp",
                "provider": "wabery",
                "note": data.get("message", f"Wabery error {resp.status_code}: {resp.text[:200]}"),
                "message_content": message,
            }
    except Exception as e:
        return {
            "message_sid": "wab_fail",
            "status": "failed",
            "channel": "whatsapp",
            "provider": "wabery",
            "note": str(e),
            "message_content": message,
        }
