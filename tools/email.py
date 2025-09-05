# ai-scheduling-agent/tools/email.py

import os
import smtplib
from dotenv import load_dotenv
from tools.utils import sanitize_email
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders

load_dotenv()

def _get_email_credentials():
    user = os.getenv("EMAIL_USER")
    password = os.getenv("EMAIL_PASSWORD")
    missing = [name for name, val in {
        "EMAIL_USER": user,
        "EMAIL_PASSWORD": password,
    }.items() if not val]
    if missing:
        raise RuntimeError(
            "Missing required email environment variables: "
            + ", ".join(missing)
            + "\nPlease set them in your .env file."
        )
    return user, password

def send_email(to_email: str, subject: str, body: str):
    from_email, password = _get_email_credentials()
    to_email_norm = sanitize_email(to_email)
    if not to_email_norm:
        raise RuntimeError(f"Invalid recipient email: {to_email}")

    msg = MIMEMultipart()
    msg['From'] = from_email
    msg['To'] = to_email_norm
    msg['Subject'] = subject or ""
    msg.attach(MIMEText(body or "", 'plain'))

    server = smtplib.SMTP('smtp.gmail.com', 587)
    server.starttls()
    server.login(from_email, password)
    server.sendmail(from_email, to_email_norm, msg.as_string())
    server.quit()

def send_email_with_attachment(to_email: str, subject: str, body: str, file_path: str):
    from_email, password = _get_email_credentials()
    to_email_norm = sanitize_email(to_email)
    if not to_email_norm:
        raise RuntimeError(f"Invalid recipient email: {to_email}")

    msg = MIMEMultipart()
    msg['From'] = from_email
    msg['To'] = to_email_norm
    msg['Subject'] = subject or ""
    msg.attach(MIMEText(body or "", 'plain'))

    try:
        with open(file_path, "rb") as attachment:
            part = MIMEBase('application', 'octet-stream')
            part.set_payload(attachment.read())
        encoders.encode_base64(part)
        part.add_header('Content-Disposition', f"attachment; filename={os.path.basename(file_path)}")
        msg.attach(part)
    except FileNotFoundError:
        print(f"Attachment not found: {file_path}")
        return

    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(from_email, password)
        server.sendmail(from_email, to_email_norm, msg.as_string())
        server.quit()
        print("Email sent successfully.")
    except Exception as e:
        print(f"Email failed: {e}")
