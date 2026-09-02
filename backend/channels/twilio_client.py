"""
RecoverAI — Channel: Twilio Client
WhatsApp, SMS, and Voice via Twilio.
"""

from twilio.rest import Client
from twilio.twiml.messaging_response import MessagingResponse
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import settings


twilio_client = Client(settings.twilio_account_sid, settings.twilio_auth_token)


def send_whatsapp(to_phone: str, message: str) -> dict:
    """Send a WhatsApp message via Wabery."""
    from channels.wabery_client import send_whatsapp as send_wabery_msg
    return send_wabery_msg(to_phone, message)



def send_sms(to_phone: str, message: str) -> dict:
    """Send an SMS message via Twilio. Falls back to trial template if trial restrictions apply."""
    try:
        msg = twilio_client.messages.create(body=message, from_=settings.twilio_phone_number, to=to_phone)
        return {"message_sid": msg.sid, "status": msg.status, "channel": "sms"}
    except Exception as e:
        error_str = str(e)
        # Error 572006: Trial accounts to India require predefined template names like 'sms_event_notifications'
        if "572006" in error_str or "Invalid template name" in error_str or "Trial accounts" in error_str:
            try:
                print(f"  ℹ️  Twilio Trial mode: Sending pre-approved template 'sms_event_notifications' to {to_phone}")
                msg = twilio_client.messages.create(body="sms_event_notifications", from_=settings.twilio_phone_number, to=to_phone)
                return {
                    "message_sid": msg.sid,
                    "status": msg.status,
                    "channel": "sms",
                    "template": "sms_event_notifications",
                    "original_message": message,
                }
            except Exception as template_err:
                error_str = str(template_err)

        return {
            "message_sid": f"sms_sim_{to_phone[-6:]}",
            "status": "simulated",
            "channel": "sms_simulated",
            "note": f"SMS error: {error_str[:100]}",
            "message_content": message,
        }


def make_voice_call(to_phone: str, twiml_script_or_text: str) -> dict:
    """Make a voice call via Twilio with automatic trial-mode twimlet fallback."""
    import urllib.parse
    import re
    try:
        # Extract plain text if XML is passed
        clean_text = re.sub(r"<[^>]+>", " ", twiml_script_or_text).strip()
        clean_text = re.sub(r"\s+", " ", clean_text)
        if not clean_text:
            clean_text = "Namaste! This is an automated payment reminder from StyleBazaar RecoverAI. Please complete your payment using the link sent to you. Thank you!"

        twimlet_url = f"http://twimlets.com/message?Message%5B0%5D={urllib.parse.quote(clean_text)}"

        # Try URL-based dispatch (fully allowed on all Twilio trial & production accounts)
        call = twilio_client.calls.create(
            url=twimlet_url,
            from_=settings.twilio_phone_number,
            to=to_phone
        )
        print(f"📞 [Twilio Voice] Outbound call placed to {to_phone} (SID: {call.sid}, Status: {call.status})")
        return {"call_sid": call.sid, "status": call.status, "channel": "voice"}
    except Exception as e:
        print(f"⚠️ [Twilio Voice] Error: {e}")
        return {
            "call_sid": f"call_sim_{to_phone[-6:]}",
            "status": "simulated",
            "channel": "voice_simulated",
            "note": f"Voice error: {str(e)[:100]}",
        }


def build_hinglish_twiml(customer_name: str, amount_rupees: int, product_name: str) -> str:
    return (
        f"Namaste {customer_name} ji! Main {settings.merchant_name} RecoverAI se bol raha hoon. "
        f"Aapka {amount_rupees} rupaye ka payment {product_name} ke liye process nahi ho paya. "
        f"Aapko ek 1-click payment link WhatsApp aur SMS par bhej diya gaya hai. "
        f"Kripya use complete karein. Dhanyavaad!"
    )


def create_whatsapp_reply(message_body: str) -> str:
    resp = MessagingResponse()
    resp.message(message_body)
    return str(resp)
