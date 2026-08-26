"""Research ingestion — batch-process company and lead data into SQLite.

This module is used by the agent to persist research findings efficiently.
It is NOT an automated scraper — the agent provides the data from its
web research tools.
"""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from . import db
from .scoring import score_company, classify_company
from .render import render_email, validate_attachment, TemplateValidationError

ATTACHMENT_PATH = "assets/erdogan_kocabas_cv.pdf"


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def ingest_company(
    conn: sqlite3.Connection,
    *,
    name: str,
    domain: str,
    website: str | None = None,
    sector: str,
    description: str | None = None,
    location: str | None = None,
    work_mode: str | None = None,
    employee_count: int | None = None,
    employee_count_confidence: str | None = None,
    funding_status: str | None = None,
    funding_details: str | None = None,
    funding_source_url: str | None = None,
    founder_quality_score: float = 0,
    company_potential_score: float = 0,
    sector_fit_score: float = 0,
    funding_traction_score: float = 0,
    rationale: str | None = None,
    founders: list[dict] | None = None,
) -> dict:
    """Ingest a company and its founders into the database.

    Returns dict with company_id, total_fit_score, classification.
    """
    total = score_company(
        founder_quality_score,
        company_potential_score,
        sector_fit_score,
        funding_traction_score,
    )
    classification = classify_company(total, funding_status)

    cid = db.upsert_company(conn, {
        "name": name,
        "domain": domain,
        "website": website or f"https://{domain}",
        "sector": sector,
        "description": description,
        "location": location,
        "work_mode": work_mode,
        "employee_count": employee_count,
        "employee_count_confidence": employee_count_confidence,
        "funding_status": funding_status,
        "funding_details": funding_details,
        "funding_source_url": funding_source_url,
        "founder_quality_score": founder_quality_score,
        "company_potential_score": company_potential_score,
        "sector_fit_score": sector_fit_score,
        "funding_traction_score": funding_traction_score,
        "total_fit_score": total,
        "classification": classification.value,
        "rationale": rationale,
        "researched_at": _now_iso(),
    })

    if founders:
        for f in founders:
            db.upsert_founder(conn, {
                "company_id": cid,
                "full_name": f["full_name"],
                "title": f.get("title"),
                "university": f.get("university"),
                "previous_companies": f.get("previous_companies"),
                "founder_quality_evidence": f.get("evidence"),
                "profile_url": f.get("profile_url"),
                "source_urls_json": json.dumps(f.get("source_urls", []), ensure_ascii=False),
            })

    return {"company_id": cid, "total_fit_score": total, "classification": classification.value}


def ingest_lead(
    conn: sqlite3.Connection,
    *,
    company_id: int,
    full_name: str,
    first_name: str,
    title: str | None = None,
    contact_priority: str | None = None,
    profile_url: str | None = None,
    honorific: str | None = None,
    honorific_confidence: str | None = None,
    honorific_evidence_url: str | None = None,
    email: str | None = None,
    email_provider: str | None = None,
    email_score: float | None = None,
    email_verification_status: str | None = None,
    email_source_urls: list[str] | None = None,
    personalization_paragraph: str | None = None,
    personalization_source_urls: list[str] | None = None,
    company_name: str | None = None,
) -> dict:
    """Ingest a lead into the database, computing eligibility and rendering email.

    Returns dict with lead_id, status, eligibility, and any errors.
    """
    errors = []
    status = "CONTACT_FOUND"
    eligibility = False

    # Check duplicate email
    if email and db.check_duplicate_email(conn, email):
        status = "SKIPPED_DUPLICATE"
        errors.append(f"Duplicate email: {email}")

    # Honorific check
    if honorific not in ("Hanım", "Bey"):
        if honorific_confidence != "high":
            status = "NEEDS_GENDER_REVIEW"
            errors.append(f"Uncertain honorific: {honorific}")

    # Email check
    if not email:
        status = "EMAIL_NOT_FOUND"
        errors.append("No email found")
    elif email_verification_status not in ("valid",):
        if email_verification_status == "invalid":
            status = "INVALID_EMAIL"
        else:
            status = "EMAIL_UNVERIFIED"
        errors.append(f"Email status: {email_verification_status}")

    # Try to render email
    rendered_body = None
    subject = None
    if (
        email
        and honorific in ("Hanım", "Bey")
        and personalization_paragraph
        and company_name
        and not errors
    ):
        try:
            subject, rendered_body = render_email(
                first_name=first_name,
                honorific=honorific,
                company_name=company_name,
                personalization_paragraph=personalization_paragraph,
            )
            status = "READY_FOR_REVIEW"
            eligibility = True
        except TemplateValidationError as e:
            errors.append(f"Template error: {e}")

    lid = db.upsert_lead(conn, {
        "company_id": company_id,
        "full_name": full_name,
        "first_name": first_name,
        "title": title,
        "contact_priority": contact_priority,
        "profile_url": profile_url,
        "honorific": honorific,
        "honorific_confidence": honorific_confidence,
        "honorific_evidence_url": honorific_evidence_url,
        "email": email,
        "email_provider": email_provider,
        "email_score": email_score,
        "email_verification_status": email_verification_status,
        "email_source_urls_json": json.dumps(email_source_urls or [], ensure_ascii=False),
        "personalization_paragraph": personalization_paragraph,
        "personalization_source_urls_json": json.dumps(personalization_source_urls or [], ensure_ascii=False),
        "subject": subject,
        "rendered_body": rendered_body,
        "attachment_path": ATTACHMENT_PATH if eligibility else None,
        "eligibility": 1 if eligibility else 0,
        "status": status,
    })

    return {
        "lead_id": lid,
        "status": status,
        "eligibility": eligibility,
        "errors": errors,
    }
