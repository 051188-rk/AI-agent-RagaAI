# test_comms.py
"""
Standalone test harness for SMS and Email.
Uses messaging.py and email.py functions.
"""

import os
from dotenv import load_dotenv
from tools.messaging import send_sms
from tools.email import send_email

load_dotenv()  # Load environment variables from .env

def test_sms():
    to_number = os.getenv("TEST_PHONE_NUMBER")
    if not to_number:
        print("⚠️ Please set TEST_PHONE_NUMBER in your .env to run SMS test.")
        return
    try:
        sid = send_sms(to_number, "Hello from AI Scheduling Agent test SMS ✅")
        print(f"📨 SMS sent successfully. Message SID: {sid}")
    except Exception as e:
        print(f"❌ SMS test failed: {e}")

def test_email():
    to_email = os.getenv("TEST_EMAIL")
    if not to_email:
        print("⚠️ Please set TEST_EMAIL in your .env to run Email test.")
        return
    try:
        send_email(to_email, "Test Email ✅", "Hello from AI Scheduling Agent test email.")
        print("📧 Email sent successfully.")
    except Exception as e:
        print(f"❌ Email test failed: {e}")

if __name__ == "__main__":
    print("=== Running Communication Tests ===")
    test_sms()
    test_email()
