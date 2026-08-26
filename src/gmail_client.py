"""Gmail API OAuth sender — MIME multipart with PDF attachment.

Uses OAuth Desktop App credentials:
- client_secret: credentials/client_secret.json
- token: credentials/token.json
- scope: gmail.send
"""

from __future__ import annotations

import base64
import logging
import mimetypes
import os
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

SCOPES = ["https://www.googleapis.com/auth/gmail.send"]


def _get_credentials_paths() -> tuple[str, str]:
    """Return (client_secret_path, token_path)."""
    client_secret = os.getenv(
        "GOOGLE_OAUTH_CLIENT_SECRET_FILE", "credentials/client_secret.json"
    )
    token_file = os.getenv("GOOGLE_OAUTH_TOKEN_FILE", "credentials/token.json")
    return client_secret, token_file


def authenticate():
    """Authenticate with Gmail API using OAuth.

    Returns a Gmail API service object.
    On first run, opens a browser for user consent.
    """
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from googleapiclient.discovery import build

    client_secret_path, token_path = _get_credentials_paths()
    creds = None

    if Path(token_path).exists():
        creds = Credentials.from_authorized_user_file(token_path, SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not Path(client_secret_path).exists():
                raise FileNotFoundError(
                    f"OAuth client secret not found at {client_secret_path}. "
                    "Download from Google Cloud Console → Credentials → OAuth 2.0 Client IDs."
                )
            flow = InstalledAppFlow.from_client_secrets_file(client_secret_path, SCOPES)
            creds = flow.run_local_server(port=0)

        Path(token_path).parent.mkdir(parents=True, exist_ok=True)
        Path(token_path).write_text(creds.to_json())

    service = build("gmail", "v1", credentials=creds)
    return service


def build_message(
    sender: str,
    to: str,
    subject: str,
    body: str,
    attachment_path: str,
) -> dict:
    """Build a MIME multipart message with PDF attachment.

    Returns the raw message dict ready for Gmail API.
    """
    msg = MIMEMultipart()
    msg["From"] = sender
    msg["To"] = to
    msg["Subject"] = subject

    # Body
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

    raw = base64.urlsafe_b64encode(msg.as_bytes()).decode("utf-8")
    return {"raw": raw}


def send_email(
    service,
    to: str,
    subject: str,
    body: str,
    attachment_path: str,
    sender: Optional[str] = None,
) -> str:
    """Send an email via Gmail API.

    Returns the Gmail message ID on success.
    Raises on failure.
    """
    if sender is None:
        sender = os.getenv("GMAIL_SENDER_EMAIL", "me")

    message = build_message(sender, to, subject, body, attachment_path)

    try:
        result = (
            service.users()
            .messages()
            .send(userId="me", body=message)
            .execute()
        )
        msg_id = result.get("id", "")
        logger.info("Sent email to %s — Gmail ID: %s", to, msg_id)
        return msg_id
    except Exception as e:
        logger.error("Failed to send email to %s: %s", to, e)
        raise
