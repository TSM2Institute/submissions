"""SMTP email utility for the TSM2 Submission Portal.

Sends email via the Institute's hosted mail server (smtp.hostedemail.com)
using TLS on port 587. Credentials come from the TSM2_INFO_EMAIL secret.

Email sending must never block or fail a submission — callers should use
send_email_async for fire-and-forget delivery after the GitHub issue
has been created.
"""

import os
import sys
import smtplib
import threading
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart


SMTP_HOST = "smtp.hostedemail.com"
SMTP_PORT = 587
SMTP_USER = "info@tsm2.org"
FROM_HEADER = "TSM2 Institute <info@tsm2.org>"


def send_email(to_address, subject, body_text, body_html=None):
    """Send an email via the Institute's SMTP server.

    Args:
        to_address: recipient email address (string)
        subject: email subject line (string)
        body_text: plain text body (string)
        body_html: optional HTML body (string)

    Returns:
        True if sent successfully, False otherwise.
    """
    smtp_pass = os.environ.get("TSM2_INFO_EMAIL", "")

    if not smtp_pass:
        print("[EMAIL ERROR] TSM2_INFO_EMAIL secret not configured", file=sys.stderr)
        return False

    if not to_address:
        print("[EMAIL ERROR] No recipient address provided", file=sys.stderr)
        return False

    try:
        msg = MIMEMultipart("alternative")
        msg["From"] = FROM_HEADER
        msg["To"] = to_address
        msg["Subject"] = subject

        msg.attach(MIMEText(body_text, "plain", "utf-8"))
        if body_html:
            msg.attach(MIMEText(body_html, "html", "utf-8"))

        with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=30) as server:
            server.starttls()
            server.login(SMTP_USER, smtp_pass)
            server.send_message(msg)

        print(f"[EMAIL] Sent to {to_address}: {subject}", file=sys.stderr)
        return True

    except Exception as e:
        print(f"[EMAIL ERROR] Failed to send to {to_address}: {e}", file=sys.stderr)
        return False


def send_email_async(to_address, subject, body_text, body_html=None):
    """Fire-and-forget email sending in a background thread."""
    thread = threading.Thread(
        target=send_email,
        args=(to_address, subject, body_text, body_html),
        daemon=True,
    )
    thread.start()
    return thread
