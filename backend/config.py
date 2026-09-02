"""
RecoverAI — Configuration
Loads all environment variables from .env file.
"""

from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # --- Supabase ---
    supabase_url: str = ""
    supabase_publishable_key: str = ""
    supabase_secret_key: str = ""
    supabase_jwks_url: str = ""

    # --- Pinecone ---
    pinecone_api_key: str = ""
    pinecone_index_name: str = "recoverai"

    # --- Razorpay ---
    razorpay_key_id: str = ""
    razorpay_key_secret: str = ""
    razorpay_webhook_secret: str = ""

    # --- Twilio ---
    twilio_account_sid: str = ""
    twilio_auth_token: str = ""
    twilio_phone_number: str = ""
    twilio_whatsapp_number: str = "whatsapp:+14155238886"

    # --- Wabery (Live Two-Way WhatsApp) ---
    wabery_api_key: str = ""
    wabery_channel_id: str = ""
    wabery_conversation_id: str = ""

    # --- MSG91 (India SMS + WhatsApp) ---
    msg91_auth_key: str = ""

    # --- Fast2SMS (Custom SMS for India) ---
    fast2sms_api_key: str = ""

    # --- Resend ---
    resend_api_key: str = ""
    resend_from_email: str = "RecoverAI <recover@yourdomain.com>"

    # --- Google AI ---
    google_api_key: str = ""
    gemini_model: str = "gemini-3.1-flash-lite"


    # --- Demo ---
    demo_phone_number: str = ""
    demo_email: str = ""
    demo_customer_name: str = "Gagan Singhal"

    # --- App ---
    merchant_name: str = "StyleBazaar"
    app_env: str = "development"
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    frontend_url: str = "http://localhost:5173"

    class Config:
        env_file = (".env", "../.env")
        env_file_encoding = "utf-8"


settings = Settings()
