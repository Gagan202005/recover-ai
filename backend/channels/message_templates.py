"""
RecoverAI — Multi-Language Message Templates
Hindi, Hinglish, English templates for all channels.
"""

from config import settings

TEMPLATES = {
    "recovery_whatsapp": {
        "hinglish": (
            "Hi {name}! 🙏 Aapka ₹{amount} ka payment {product} ke liye fail ho gaya.\n"
            "Yahan se complete karein: {link}\n"
            "Reply STOP to opt out."
        ),
        "english": (
            "Hi {name}! Your payment of ₹{amount} for {product} couldn't be processed.\n"
            "Complete it here: {link}\n"
            "Reply STOP to opt out."
        ),
        "hindi": (
            "नमस्ते {name} जी! 🙏 आपका ₹{amount} का भुगतान {product} के लिए प्रोसेस नहीं हो पाया।\n"
            "यहाँ से पूरा करें: {link}\n"
            "ऑप्ट आउट के लिए STOP टाइप करें।"
        ),
    },
    "recovery_sms": {
        "hinglish": (
            "{merchant}: Hi {name}, aapka Rs.{amount} ka payment fail hua. "
            "Complete karein: {link} Reply STOP to opt out."
        ),
        "english": (
            "{merchant}: Hi {name}, your Rs.{amount} payment failed. "
            "Complete here: {link} Reply STOP to opt out."
        ),
        "hindi": (
            "{merchant}: नमस्ते {name}, आपका Rs.{amount} का भुगतान विफल हुआ। "
            "यहाँ पूरा करें: {link} STOP टाइप करें।"
        ),
    },
    "recovery_email_subject": {
        "hinglish": "Aapka ₹{amount} ka payment complete karein — {merchant}",
        "english": "Complete your ₹{amount} purchase — {merchant}",
        "hindi": "आपका ₹{amount} का भुगतान पूरा करें — {merchant}",
    },
    "promise_ack": {
        "hinglish": "Koi baat nahi {name}! 🙏 Hum aapko {date} ko remind karenge. Aapka link tab tak active rahega. 👍",
        "english": "No worries {name}! 🙏 We'll remind you on {date}. Your link stays active. 👍",
        "hindi": "कोई बात नहीं {name} जी! 🙏 हम आपको {date} को याद दिलाएंगे। आपका लिंक तब तक सक्रिय रहेगा। 👍",
    },
    "will_pay_now": {
        "hinglish": "Bahut badhiya {name}! 🎉 Yeh raha aapka payment link: {link}",
        "english": "Great {name}! 🎉 Here's your payment link: {link}",
        "hindi": "बहुत बढ़िया {name} जी! 🎉 यह रहा आपका पेमेंट लिंक: {link}",
    },
    "opt_out_ack": {
        "hinglish": "Samajh gaye {name}. Hum aapko aur messages nahi bhejenge. 🙏",
        "english": "Understood {name}. We won't send you any more messages. 🙏",
        "hindi": "समझ गए {name} जी। हम आपको और मैसेज नहीं भेजेंगे। 🙏",
    },
    "need_help": {
        "hinglish": "Hi {name}! Aapka payment {reason} ki wajah se fail hua. Koi bhi sawal ho toh yahan reply karein. 🙏",
        "english": "Hi {name}! Your payment failed due to {reason}. Feel free to reply here with questions. 🙏",
        "hindi": "नमस्ते {name} जी! आपका भुगतान {reason} के कारण विफल हुआ। कोई भी सवाल हो तो यहाँ रिप्लाई करें। 🙏",
    },
}

# City → Language mapping
CITY_LANGUAGE_MAP = {
    "Mumbai": "hinglish", "Delhi": "hinglish", "Pune": "hinglish",
    "Ahmedabad": "hinglish", "Noida": "hinglish", "Gurgaon": "hinglish",
    "Bangalore": "english", "Chennai": "english", "Hyderabad": "english",
    "Kolkata": "english", "Kochi": "english",
    "Lucknow": "hindi", "Jaipur": "hindi", "Varanasi": "hindi",
    "Bhopal": "hindi", "Patna": "hindi", "Indore": "hindi",
}


def select_language(customer: dict) -> str:
    """Select message language based on customer profile."""
    if customer.get("preferred_language"):
        return customer["preferred_language"]
    city = customer.get("city", "")
    return CITY_LANGUAGE_MAP.get(city, "english")


def render_template(template_key: str, language: str, **kwargs) -> str:
    """Render a message template with the given language and variables."""
    templates = TEMPLATES.get(template_key, {})
    template = templates.get(language, templates.get("english", ""))
    kwargs.setdefault("merchant", settings.merchant_name)
    return template.format(**kwargs)
