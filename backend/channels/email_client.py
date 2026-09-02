"""
RecoverAI — Channel: Email Client
Transactional email via Resend.
"""

import resend
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import settings

resend.api_key = settings.resend_api_key


def send_email(to_email: str, subject: str, html_body: str) -> dict:
    email = resend.Emails.send({"from": settings.resend_from_email, "to": to_email, "subject": subject, "html": html_body})
    return {"message_id": email["id"], "channel": "email"}


def build_recovery_email_html(customer_name: str, amount_display: str, product_name: str,
                                payment_link: str, merchant_name: str) -> str:
    return f"""
    <!DOCTYPE html>
    <html>
    <body style="font-family:'Inter','Segoe UI',sans-serif;background:#0f0f0f;color:#e0e0e0;padding:40px;">
      <div style="max-width:600px;margin:0 auto;background:#1a1a2e;border-radius:16px;padding:40px;border:1px solid #2a2a4a;">
        <div style="text-align:center;margin-bottom:24px;">
          <h1 style="color:#818cf8;margin:0;font-size:24px;">{merchant_name}</h1>
        </div>
        <h2 style="color:#f0f0f0;font-size:20px;">Hi {customer_name}! 👋</h2>
        <p style="font-size:16px;line-height:1.6;color:#c0c0c0;">
          Your payment of <strong style="color:#34d399;">{amount_display}</strong> for
          <strong>{product_name}</strong> couldn't be processed.
        </p>
        <p style="font-size:16px;line-height:1.6;color:#c0c0c0;">No worries — complete it with one click:</p>
        <div style="text-align:center;margin:32px 0;">
          <a href="{payment_link}"
             style="background:linear-gradient(135deg,#818cf8,#6366f1);color:white;
                    padding:16px 40px;border-radius:12px;text-decoration:none;
                    font-size:18px;font-weight:600;display:inline-block;
                    box-shadow:0 4px 15px rgba(99,102,241,0.4);">
            💳 Complete Payment
          </a>
        </div>
        <p style="color:#888;font-size:13px;margin-top:32px;text-align:center;">
          Link expires in 24 hours. Reply STOP to opt out.
        </p>
        <hr style="border:none;border-top:1px solid #2a2a4a;margin:24px 0;">
        <p style="color:#666;font-size:11px;text-align:center;">Powered by RecoverAI</p>
      </div>
    </body>
    </html>"""
