"""Gmail SMTP Sender using App Password."""

from __future__ import annotations

import logging
import mimetypes
import os
import smtplib
import uuid
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)


def send_smtp_email(
    to: str,
    subject: str,
    body: str,
    attachment_path: str = "assets/erdogan_kocabas_cv.pdf",
    sender_email: Optional[str] = None,
    app_password: Optional[str] = None,
) -> str:
    sender = sender_email or os.getenv("GMAIL_SENDER_EMAIL", "").strip()
    password = (app_password or os.getenv("GMAIL_APP_PASSWORD", "")).replace(" ", "").strip()

    if not sender or not password:
        raise ValueError("GMAIL_SENDER_EMAIL and GMAIL_APP_PASSWORD must be configured.")

    msg = MIMEMultipart()
    msg["From"] = sender
    msg["To"] = to
    msg["Subject"] = subject

    # Body text
    msg.attach(MIMEText(body, "plain", "utf-8"))

    # Attachment
    att_path = Path(attachment_path)
    if not att_path.exists():
        raise FileNotFoundError(f"Attachment not found: {attachment_path}")

    content_type, _ = mimetypes.guess_type(str(att_path))
    if content_type is None:
        content_type = "application/octet-stream"

    with open(att_path, "rb") as f:
        attachment = MIMEApplication(f.read(), _subtype="pdf")
        attachment.add_header(
            "Content-Disposition", "attachment", filename=att_path.name
        )
        msg.attach(attachment)

    # Send via SMTP SSL
    server = smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=30)
    server.login(sender, password)
    server.sendmail(sender, [to], msg.as_string())
    server.quit()

    msg_id = f"smtp-{uuid.uuid4().hex[:12]}"
    logger.info("Successfully sent SMTP email to %s (ID: %s)", to, msg_id)
    return msg_id
