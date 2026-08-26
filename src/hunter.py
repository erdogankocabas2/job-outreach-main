"""Hunter.io API client — email finding and verification.

Rules from config/campaign.yaml:
- eligible_statuses: [valid]
- accept_all_enabled: false
- minimum_score: 90
- allow_pattern_guessing: false
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

HUNTER_BASE = "https://api.hunter.io/v2"


@dataclass
class HunterResult:
    email: Optional[str] = None
    score: Optional[int] = None
    status: Optional[str] = None  # valid, invalid, accept_all, unknown
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    position: Optional[str] = None
    sources: Optional[list[dict]] = None
    raw: Optional[dict] = None


def _get_api_key() -> str:
    key = os.getenv("HUNTER_API_KEY", "").strip()
    if not key:
        raise RuntimeError("HUNTER_API_KEY not set in environment")
    return key


def find_email(
    domain: str,
    first_name: str,
    last_name: str,
    *,
    min_score: int = 90,
    accept_all_ok: bool = False,
    eligible_statuses: list[str] | None = None,
) -> HunterResult:
    """Find an email for a person at a company domain.

    Returns a HunterResult. The caller must check .email and .status
    to determine eligibility.
    """
    if eligible_statuses is None:
        eligible_statuses = ["valid"]

    api_key = _get_api_key()
    params = {
        "domain": domain,
        "first_name": first_name,
        "last_name": last_name,
        "api_key": api_key,
    }

    try:
        resp = requests.get(f"{HUNTER_BASE}/email-finder", params=params, timeout=15)
        resp.raise_for_status()
        data = resp.json().get("data", {})
    except requests.RequestException as e:
        logger.error("Hunter email-finder failed for %s %s @ %s: %s", first_name, last_name, domain, e)
        return HunterResult(raw={"error": str(e)})

    result = HunterResult(
        email=data.get("email"),
        score=data.get("score"),
        status=data.get("verification", {}).get("status") if data.get("verification") else None,
        first_name=data.get("first_name"),
        last_name=data.get("last_name"),
        position=data.get("position"),
        sources=data.get("sources"),
        raw=data,
    )

    # If no verification status in finder, the score alone may hint.
    # We only trust results that pass our rules:
    if result.email:
        # Reject personal/webmail
        personal_domains = {
            "gmail.com", "yahoo.com", "hotmail.com", "outlook.com",
            "yandex.com", "icloud.com", "mail.com", "protonmail.com",
        }
        email_domain = result.email.split("@")[-1].lower()
        if email_domain in personal_domains:
            logger.info("Rejected personal email: %s", result.email)
            result.email = None
            result.status = "personal_webmail"
            return result

        # Score check
        if result.score is not None and result.score < min_score:
            logger.info("Score %d below min %d for %s", result.score, min_score, result.email)
            result.status = "low_score"

    return result


def verify_email(
    email: str,
    *,
    min_score: int = 90,
    accept_all_ok: bool = False,
    eligible_statuses: list[str] | None = None,
) -> HunterResult:
    """Verify a known email address.

    Returns a HunterResult with updated verification status.
    """
    if eligible_statuses is None:
        eligible_statuses = ["valid"]

    api_key = _get_api_key()
    params = {"email": email, "api_key": api_key}

    try:
        resp = requests.get(f"{HUNTER_BASE}/email-verifier", params=params, timeout=15)
        resp.raise_for_status()
        data = resp.json().get("data", {})
    except requests.RequestException as e:
        logger.error("Hunter email-verifier failed for %s: %s", email, e)
        return HunterResult(email=email, raw={"error": str(e)})

    result = HunterResult(
        email=data.get("email"),
        score=data.get("score"),
        status=data.get("status"),  # valid, invalid, accept_all, unknown
        raw=data,
    )

    # Check eligibility
    if result.status not in eligible_statuses:
        if result.status == "accept_all" and not accept_all_ok:
            logger.info("accept_all not accepted for %s", email)
        elif result.status:
            logger.info("Status '%s' not eligible for %s", result.status, email)

    if result.score is not None and result.score < min_score:
        logger.info("Verification score %d below min %d for %s", result.score, min_score, email)

    return result


def is_eligible(
    result: HunterResult,
    *,
    min_score: int = 90,
    accept_all_ok: bool = False,
    eligible_statuses: list[str] | None = None,
) -> bool:
    """Check if a Hunter result meets all eligibility criteria."""
    if eligible_statuses is None:
        eligible_statuses = ["valid"]

    if not result.email:
        return False
    if result.status not in eligible_statuses:
        return False
    if result.status == "accept_all" and not accept_all_ok:
        return False
    if result.score is not None and result.score < min_score:
        return False
    return True
