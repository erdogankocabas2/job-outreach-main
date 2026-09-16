"""Hunter.io API client for domain search, email finder, and email verification."""

from __future__ import annotations

import logging
import os
import requests
from typing import Any, Optional
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger("hunter_client")
BASE_URL = "https://api.hunter.io/v2"


def get_api_key() -> str:
    key = os.getenv("HUNTER_API_KEY", "").strip()
    if not key:
        raise ValueError("HUNTER_API_KEY not set in .env")
    return key


def check_account() -> dict[str, Any]:
    """Check Hunter API account status and remaining credits."""
    api_key = get_api_key()
    resp = requests.get(f"{BASE_URL}/account", params={"api_key": api_key}, timeout=10)
    resp.raise_for_status()
    return resp.json().get("data", {})


def search_domain(domain: str, limit: int = 10, department: Optional[str] = None) -> dict[str, Any]:
    """Search domain for email pattern and known employees.
    
    department options: executive, hr, management, communication, etc.
    """
    api_key = get_api_key()
    params = {
        "domain": domain,
        "api_key": api_key,
        "limit": limit,
    }
    if department:
        params["department"] = department

    resp = requests.get(f"{BASE_URL}/domain-search", params=params, timeout=10)
    if resp.status_code == 400 or resp.status_code == 404:
        return {}
    resp.raise_for_status()
    return resp.json().get("data", {})


def find_email(domain: str, first_name: str, last_name: str, company: Optional[str] = None) -> dict[str, Any]:
    """Find specific email using domain and full name."""
    api_key = get_api_key()
    params = {
        "domain": domain,
        "first_name": first_name,
        "last_name": last_name,
        "api_key": api_key,
    }
    if company:
        params["company"] = company

    resp = requests.get(f"{BASE_URL}/email-finder", params=params, timeout=10)
    if resp.status_code == 404:
        return {}
    resp.raise_for_status()
    return resp.json().get("data", {})


def verify_email(email: str) -> dict[str, Any]:
    """Verify deliverability of an email."""
    api_key = get_api_key()
    params = {
        "email": email,
        "api_key": api_key,
    }
    resp = requests.get(f"{BASE_URL}/email-verifier", params=params, timeout=10)
    if resp.status_code == 404:
        return {}
    resp.raise_for_status()
    return resp.json().get("data", {})
