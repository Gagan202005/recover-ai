"""
RecoverAI — MCP Server: Communications
5 tools for WhatsApp, SMS, Email, Voice, and DND check via MCP.
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from mcp.server.fastmcp import FastMCP
from channels.twilio_client import make_voice_call
from channels.wabery_client import send_whatsapp
from channels.sms_router import dispatch_sms
from channels.email_client import send_email
from database import supabase

mcp = FastMCP("comms-recovery")


@mcp.tool()
def tool_send_whatsapp(to_phone: str, message: str) -> dict:
    """Send a custom WhatsApp message via Wabery.
    Supports real-time two-way messaging and payment recovery links.
    Returns real message SID."""
    result = send_whatsapp(to_phone=to_phone, message=message)
    return result


@mcp.tool()
def tool_send_sms(to_phone: str, message: str) -> dict:
    """Send an SMS via Twilio.
    Phone must include country code.
    Returns real Twilio message SID."""
    result = send_sms(to_phone=to_phone, message=message)
    return result


@mcp.tool()
def tool_send_email(to_email: str, subject: str, html_body: str) -> dict:
    """Send an email via Resend.
    html_body should contain styled HTML content.
    Returns real Resend message ID."""
    result = send_email(to_email=to_email, subject=subject, html_body=html_body)
    return result


@mcp.tool()
def tool_make_voice_call(to_phone: str, twiml_script: str) -> dict:
    """Make a voice call with TTS via Twilio.
    twiml_script should be a valid TwiML XML string.
    Returns real Twilio call SID."""
    result = make_voice_call(to_phone=to_phone, twiml_script=twiml_script)
    return result


@mcp.tool()
def tool_check_dnd_status(phone: str) -> dict:
    """Check if a phone number is on the TRAI DND registry.
    Returns {phone, on_dnd: bool}."""
    try:
        result = supabase.table("customers").select("on_dnd, opted_out").eq("phone", phone).single().execute()
        return {
            "phone": phone,
            "on_dnd": result.data.get("on_dnd", False),
            "opted_out": result.data.get("opted_out", False),
        }
    except Exception:
        return {"phone": phone, "on_dnd": False, "opted_out": False}


if __name__ == "__main__":
    mcp.run()
