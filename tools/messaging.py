import os
from twilio.rest import Client

def _twilio_client():
    sid = os.environ.get("TWILIO_ACCOUNT_SID")
    token = os.environ.get("TWILIO_AUTH_TOKEN")
    if not sid or not token:
        raise RuntimeError("Twilio credentials not set in environment (.env).")
    return Client(sid, token)

def send_sms(to_number: str, body: str):
    client = _twilio_client()
    from_number = os.environ.get("TWILIO_FROM_NUMBER")
    if not from_number:
        raise RuntimeError("TWILIO_FROM_NUMBER not set")
    msg = client.messages.create(
        body=body,
        from_=from_number,
        to=to_number
    )
    return msg.sid
