# ai-scheduling-agent/tools/messaging.py

import os
import re
from dotenv import load_dotenv
from twilio.rest import Client

load_dotenv()  # Load .env variables

def _get_twilio_client():
    sid = os.getenv("TWILIO_ACCOUNT_SID")
    token = os.getenv("TWILIO_AUTH_TOKEN")
    from_number = os.getenv("TWILIO_FROM_NUMBER")

    missing = [name for name, val in {
        "TWILIO_ACCOUNT_SID": sid,
        "TWILIO_AUTH_TOKEN": token,
        "TWILIO_FROM_NUMBER": from_number,
    }.items() if not val]

    if missing:
        raise RuntimeError(
            "Missing required environment variables: "
            + ", ".join(missing)
            + "\nPlease set them in your .env file at project root."
        )

    return Client(sid, token), from_number

def _normalize_phone(raw: str, default_country_code: str = None) -> str:
    """
    Normalize phone numbers to E.164 format.
    Uses DEFAULT_COUNTRY_CODE from .env if provided (fallback +91).
    """
    if not raw:
        return None
    default_country_code = default_country_code or os.getenv("DEFAULT_COUNTRY_CODE", "+91")
    s = re.sub(r"[\s\-()]+", "", str(raw))
    if s.startswith('+'):
        return s
    digits = re.sub(r"\D", "", s)
    cc = default_country_code.lstrip('+')
    if digits.startswith(cc) and len(digits) > len(cc):
        return f"+{digits}"
    if len(digits) == 10:
        return f"+{cc}{digits}"
    if len(digits) == 11 and digits.startswith('0'):
        return f"+{cc}{digits[1:]}"
    if 8 <= len(digits) <= 15:
        return f"+{digits}"
    return None

def send_sms(to_number: str, body: str) -> str:
    client, from_number = _get_twilio_client()
    normalized_to = _normalize_phone(to_number)
    if not normalized_to or not re.fullmatch(r"\+\d{8,15}", normalized_to):
        raise RuntimeError(f"Invalid destination phone number: {to_number}")
    msg = client.messages.create(
        body=body,
        from_=from_number,
        to=normalized_to
    )
    return msg.sid
