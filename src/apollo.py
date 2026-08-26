"""Apollo.io fallback enrichment client.

Optional — only activated when APOLLO_API_KEY is present in environment.
Used as fallback when Hunter cannot return an eligible professional email.
"""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from typing import Optional

import requests
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

APOLLO_BASE = "https://api.apollo.io/v1"

PERSONAL_DOMAINS = {
    "gmail.com", "yahoo.com", "hotmail.com", "outlook.com",
    "yandex.com", "icloud.com", "mail.com", "protonmail.com",
}


@dataclass
class ApolloResult:
    email: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    title: Optional[str] = None
    organization_name: Optional[str] = None
    email_status: Optional[str] = None
    raw: Optional[dict] = None


def is_available() -> bool:
    """Check if Apollo API key is configured."""
    return bool(os.getenv("APOLLO_API_KEY", "").strip())


def _get_api_key() -> str:
    key = os.getenv("APOLLO_API_KEY", "").strip()
    if not key:
        raise RuntimeError("APOLLO_API_KEY not set in environment")
    return key


def find_person_email(
    first_name: str,
    last_name: str,
    domain: str,
    *,
    title: str | None = None,
) -> ApolloResult:
    """Search Apollo for a person's professional email.

    Returns an ApolloResult. Only professional (non-webmail) emails
    are considered valid.
    """
    if not is_available():
        return ApolloResult()

    api_key = _get_api_key()
    headers = {
        "Content-Type": "application/json",
        "Cache-Control": "no-cache",
    }
    payload = {
        "api_key": api_key,
        "first_name": first_name,
        "last_name": last_name,
        "organization_name": domain,
        "reveal_personal_emails": False,
    }

    try:
        resp = requests.post(
            f"{APOLLO_BASE}/people/match",
            json=payload,
            headers=headers,
            timeout=15,
        )
        resp.raise_for_status()
        data = resp.json().get("person", {}) or {}
    except requests.RequestException as e:
        logger.error("Apollo people/match failed for %s %s @ %s: %s", first_name, last_name, domain, e)
        return ApolloResult(raw={"error": str(e)})

    email = data.get("email")
    result = ApolloResult(
        email=email,
        first_name=data.get("first_name"),
        last_name=data.get("last_name"),
        title=data.get("title"),
        organization_name=data.get("organization", {}).get("name") if data.get("organization") else None,
        email_status=data.get("email_status"),
        raw=data,
    )

    # Reject personal/webmail
    if result.email:
        email_domain = result.email.split("@")[-1].lower()
        if email_domain in PERSONAL_DOMAINS:
            logger.info("Apollo: rejected personal email %s", result.email)
            result.email = None
            result.email_status = "personal_webmail"

    return result


def is_eligible(result: ApolloResult) -> bool:
    """Check if an Apollo result has a usable professional email."""
    if not result.email:
        return False
    if result.email_status and result.email_status not in ("verified", "guessed"):
        return False
    email_domain = result.email.split("@")[-1].lower()
    if email_domain in PERSONAL_DOMAINS:
        return False
    return True
