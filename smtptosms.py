import os
import smtplib
from email import encoders
from email.mime.base import MIMEBase
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv

load_dotenv()

SENDER_EMAIL = os.getenv("SENDER_EMAIL")
SENDER_PASSWORD = os.getenv("SENDER_PASSWORD")
SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))

OUTLOOK_SENDER_EMAIL = os.getenv("OUTLOOK_SENDER_EMAIL")
OUTLOOK_SENDER_PASSWORD = os.getenv("OUTLOOK_SENDER_PASSWORD")
OUTLOOK_SMTP_SERVER = os.getenv("OUTLOOK_SMTP_SERVER", "smtp.office365.com")
OUTLOOK_SMTP_PORT = int(os.getenv("OUTLOOK_SMTP_PORT", "587"))

RECIPIENT_HOST = os.getenv("RECIPIENT_HOST")
RECIPIENT_CARRIER_GATEWAY = os.getenv("RECIPIENT_CARRIER_GATEWAY")
RECIPIENT_EMAIL = f"{RECIPIENT_HOST}@{RECIPIENT_CARRIER_GATEWAY}"
APP_BASE_URL = os.getenv("APP_BASE_URL", "http://localhost:5000")


def send_message(
    recipient: str = None,
    tkt_id: str = "",
    subject: str = "",
    body: str = "",
    isoutlook: bool = True,
    attachment_data: bytes = None,
    attachment_filename: str = None,
) -> None:
    to_addr = recipient or RECIPIENT_EMAIL

    msg = MIMEMultipart()
    msg["From"] = OUTLOOK_SENDER_EMAIL if isoutlook else SENDER_EMAIL
    msg["To"] = to_addr
    msg["Subject"] = "Service Schedule Notification" if not subject else subject

    if body:
        body_text = body
    else:
        body_parts = ["Service schedule notification from Conformance Manager."]
        if tkt_id:
            body_parts.append(f"Ticket ID: {tkt_id}")
        if subject:
            body_parts.append(f"Subject: {subject}")
        body_parts.append(f"Link: {APP_BASE_URL}/Tickets")
        body_text = "\n".join(body_parts)

    msg.attach(MIMEText(body_text, "plain"))

    if attachment_data and attachment_filename:
        part = MIMEBase("application", "octet-stream")
        part.set_payload(attachment_data)
        encoders.encode_base64(part)
        part.add_header("Content-Disposition", f'attachment; filename="{attachment_filename}"')
        msg.attach(part)

    if isoutlook:
        smtp_server = OUTLOOK_SMTP_SERVER
        smtp_port = OUTLOOK_SMTP_PORT
        login_email = OUTLOOK_SENDER_EMAIL
        login_password = OUTLOOK_SENDER_PASSWORD
    else:
        smtp_server = SMTP_SERVER
        smtp_port = SMTP_PORT
        login_email = SENDER_EMAIL
        login_password = SENDER_PASSWORD

    with smtplib.SMTP(smtp_server, smtp_port) as server:
        server.starttls()
        server.login(login_email, login_password)
        server.sendmail(login_email, to_addr, msg.as_string())
