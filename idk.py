from twilio.rest import Client
import os
from dotenv import load_dotenv

load_dotenv()  # Loads variables from .env into process environment

# Fetch required environment variables safely
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
        + "\nPlease set them in your .env file located at the project root."
    )

client = Client(sid, token)

message = client.messages.create(
    body="Hello from Twilio test!",
    from_=from_number,
    to="+919937352247"
)

print("Message SID:", message.sid)
