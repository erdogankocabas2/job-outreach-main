"""Campaign lifecycle — snapshot, approval, state transitions, preview generation."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from . import db
from .models import CampaignStatus, LeadStatus

SNAPSHOT_PATH = Path("data/campaign_snapshot.json")
PREVIEW_PATH = Path("exports/review_preview.md")


def freeze_snapshot(conn, campaign_id: int) -> str:
    """Serialize all eligible leads into a JSON snapshot with a SHA-256 hash.

    Returns the snapshot hash.
    """
    leads = db.get_eligible_leads(conn)
    snapshot = {
        "campaign_id": campaign_id,
        "frozen_at": datetime.now(timezone.utc).isoformat(),
        "lead_count": len(leads),
        "leads": leads,
    }

    SNAPSHOT_PATH.parent.mkdir(parents=True, exist_ok=True)
    snapshot_json = json.dumps(snapshot, ensure_ascii=False, indent=2, default=str)
    SNAPSHOT_PATH.write_text(snapshot_json, encoding="utf-8")

    snapshot_hash = hashlib.sha256(snapshot_json.encode()).hexdigest()

    db.update_campaign(conn, campaign_id, {
        "snapshot_hash": snapshot_hash,
        "status": CampaignStatus.AWAITING_APPROVAL.value,
    })

    return snapshot_hash


def load_snapshot() -> dict:
    """Load the frozen snapshot from disk."""
    if not SNAPSHOT_PATH.exists():
        raise FileNotFoundError(f"Snapshot not found at {SNAPSHOT_PATH}")
    return json.loads(SNAPSHOT_PATH.read_text(encoding="utf-8"))


def verify_snapshot_hash(snapshot_path: Path = SNAPSHOT_PATH, expected_hash: str = "") -> bool:
    """Verify the snapshot file matches the expected hash."""
    if not snapshot_path.exists():
        return False
    content = snapshot_path.read_text(encoding="utf-8")
    actual_hash = hashlib.sha256(content.encode()).hexdigest()
    return actual_hash == expected_hash


def select_preview(conn, campaign_id: int, count: int = 5) -> list[dict]:
    """Select representative leads spanning different sectors and contact roles.

    Picks leads to maximize diversity across sector and contact_priority.
    """
    leads = db.get_eligible_leads(conn)
    if len(leads) <= count:
        return leads

    # Group by sector
    by_sector: dict[str, list[dict]] = {}
    for lead in leads:
        sector = lead.get("company_sector", "Unknown")
        by_sector.setdefault(sector, []).append(lead)

    selected = []
    seen_roles = set()
    seen_sectors = set()

    # Round-robin across sectors, preferring diverse roles
    sector_keys = list(by_sector.keys())
    idx = 0
    while len(selected) < count:
        sector = sector_keys[idx % len(sector_keys)]
        candidates = by_sector[sector]

        # Prefer a role we haven't seen yet
        picked = None
        for c in candidates:
            role = c.get("contact_priority", "")
            if role not in seen_roles and c["id"] not in {s["id"] for s in selected}:
                picked = c
                seen_roles.add(role)
                break

        # Fallback: any unpicked candidate from this sector
        if not picked:
            for c in candidates:
                if c["id"] not in {s["id"] for s in selected}:
                    picked = c
                    break

        if picked:
            selected.append(picked)
            seen_sectors.add(sector)

        idx += 1
        if idx > len(leads) * 2:
            break

    return selected[:count]


def write_review_preview(leads: list[dict]) -> Path:
    """Write the 5-email review preview to exports/review_preview.md."""
    PREVIEW_PATH.parent.mkdir(parents=True, exist_ok=True)

    lines = ["# Campaign Preview — 5 Representative Emails\n"]
    lines.append(f"Generated: {datetime.now(timezone.utc).isoformat()}\n")
    lines.append("---\n")

    for i, lead in enumerate(leads, 1):
        lines.append(f"## Email {i}: {lead.get('full_name', 'N/A')} @ {lead.get('company_name', 'N/A')}\n")
        lines.append(f"- **Sector:** {lead.get('company_sector', 'N/A')}")
        lines.append(f"- **Role:** {lead.get('title', 'N/A')} ({lead.get('contact_priority', 'N/A')})")
        lines.append(f"- **Email:** {lead.get('email', 'N/A')}")
        lines.append(f"- **Honorific:** {lead.get('honorific', 'N/A')}")
        lines.append(f"- **Email Score:** {lead.get('email_score', 'N/A')}")
        lines.append(f"- **Verification:** {lead.get('email_verification_status', 'N/A')}")
        lines.append("")
        lines.append("### Subject")
        lines.append(f"```\n{lead.get('subject', 'N/A')}\n```\n")
        lines.append("### Body")
        lines.append(f"```\n{lead.get('rendered_body', 'N/A')}\n```\n")
        lines.append(f"### Personalization Sources")
        sources = lead.get("personalization_source_urls_json", "[]")
        lines.append(f"```json\n{sources}\n```\n")
        lines.append("---\n")

    content = "\n".join(lines)
    PREVIEW_PATH.write_text(content, encoding="utf-8")
    return PREVIEW_PATH


def approve_campaign(conn, campaign_id: int) -> bool:
    """Set campaign as approved.

    Returns True if approval succeeds.
    Requires: snapshot hash exists and matches frozen file.
    """
    campaign = db.get_campaign(conn, campaign_id)
    if not campaign:
        raise ValueError(f"Campaign {campaign_id} not found")

    snapshot_hash = campaign.get("snapshot_hash")
    if not snapshot_hash:
        raise ValueError("No snapshot hash — freeze snapshot first")

    if not verify_snapshot_hash(expected_hash=snapshot_hash):
        raise ValueError("Snapshot hash mismatch — snapshot may have been modified")

    db.update_campaign(conn, campaign_id, {
        "approved": 1,
        "approved_at": datetime.now(timezone.utc).isoformat(),
        "status": CampaignStatus.APPROVED.value,
    })

    # Update all eligible leads to APPROVED
    conn.execute("""
        UPDATE leads SET status = ?
        WHERE eligibility = 1 AND status IN ('READY_FOR_REVIEW', 'IN_PREVIEW')
    """, (LeadStatus.APPROVED.value,))
    conn.commit()

    return True


def invalidate_approval(conn, campaign_id: int) -> None:
    """Reset approval if emails are modified after approval."""
    db.update_campaign(conn, campaign_id, {
        "approved": 0,
        "approved_at": None,
        "status": CampaignStatus.AWAITING_APPROVAL.value,
    })

    conn.execute("""
        UPDATE leads SET status = ?
        WHERE status = 'APPROVED'
    """, (LeadStatus.READY_FOR_REVIEW.value,))
    conn.commit()


def check_send_preconditions(conn, campaign_id: int) -> list[str]:
    """Verify all preconditions before scheduling/sending.

    Returns list of blocking issues (empty = ready to send).
    """
    issues = []
    campaign = db.get_campaign(conn, campaign_id)

    if not campaign:
        issues.append("Campaign not found")
        return issues

    if not campaign.get("approved"):
        issues.append("Campaign not approved")

    if not campaign.get("snapshot_hash"):
        issues.append("No snapshot hash")
    elif not verify_snapshot_hash(expected_hash=campaign["snapshot_hash"]):
        issues.append("Snapshot hash mismatch — snapshot may have been modified")

    if not campaign.get("scheduled_start"):
        issues.append("No scheduled start time configured")

    cv_path = Path("assets/erdogan_kocabas_cv.pdf")
    if not cv_path.exists():
        issues.append("CV attachment not found")

    return issues
