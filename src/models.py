"""Pydantic models and enums for the job-outreach project."""

from __future__ import annotations

import enum
from datetime import datetime
from pathlib import Path
from typing import Optional

import yaml
from pydantic import BaseModel, Field, field_validator


# ── Enums (mirror docs/state-machine.md) ──────────────────────────────────


class CompanyStatus(str, enum.Enum):
    DISCOVERED = "DISCOVERED"
    RESEARCHED = "RESEARCHED"
    OUTREACH = "OUTREACH"
    WATCHLIST = "WATCHLIST"
    REJECT = "REJECT"


class LeadStatus(str, enum.Enum):
    CONTACT_FOUND = "CONTACT_FOUND"
    NEEDS_GENDER_REVIEW = "NEEDS_GENDER_REVIEW"
    EMAIL_NOT_FOUND = "EMAIL_NOT_FOUND"
    EMAIL_UNVERIFIED = "EMAIL_UNVERIFIED"
    INVALID_EMAIL = "INVALID_EMAIL"
    READY_FOR_REVIEW = "READY_FOR_REVIEW"
    IN_PREVIEW = "IN_PREVIEW"
    APPROVED = "APPROVED"
    SCHEDULED = "SCHEDULED"
    SENT = "SENT"
    FAILED = "FAILED"
    SKIPPED_DUPLICATE = "SKIPPED_DUPLICATE"


class CampaignStatus(str, enum.Enum):
    BUILDING = "BUILDING"
    AWAITING_APPROVAL = "AWAITING_APPROVAL"
    APPROVED = "APPROVED"
    SCHEDULED = "SCHEDULED"
    SENDING = "SENDING"
    COMPLETED = "COMPLETED"
    PARTIAL_FAILURE = "PARTIAL_FAILURE"


class Honorific(str, enum.Enum):
    HANIM = "Hanım"
    BEY = "Bey"


# ── Domain models ─────────────────────────────────────────────────────────


class Company(BaseModel):
    id: Optional[int] = None
    name: str
    website: Optional[str] = None
    domain: Optional[str] = None
    sector: Optional[str] = None
    description: Optional[str] = None
    location: Optional[str] = None
    work_mode: Optional[str] = None
    employee_count: Optional[int] = None
    employee_count_confidence: Optional[str] = None
    funding_status: Optional[str] = None
    funding_details: Optional[str] = None
    funding_source_url: Optional[str] = None
    founder_quality_score: Optional[float] = None
    company_potential_score: Optional[float] = None
    sector_fit_score: Optional[float] = None
    funding_traction_score: Optional[float] = None
    total_fit_score: Optional[float] = None
    classification: Optional[str] = None
    rationale: Optional[str] = None
    researched_at: Optional[str] = None


class Founder(BaseModel):
    id: Optional[int] = None
    company_id: int
    full_name: str
    title: Optional[str] = None
    university: Optional[str] = None
    previous_companies: Optional[str] = None
    founder_quality_evidence: Optional[str] = None
    profile_url: Optional[str] = None
    source_urls_json: Optional[str] = None


class Lead(BaseModel):
    id: Optional[int] = None
    company_id: int
    full_name: str
    first_name: str
    title: Optional[str] = None
    contact_priority: Optional[str] = None
    profile_url: Optional[str] = None
    honorific: Optional[str] = None
    honorific_confidence: Optional[str] = None
    honorific_evidence_url: Optional[str] = None
    email: Optional[str] = None
    email_provider: Optional[str] = None
    email_score: Optional[float] = None
    email_verification_status: Optional[str] = None
    email_source_urls_json: Optional[str] = None
    personalization_paragraph: Optional[str] = None
    personalization_source_urls_json: Optional[str] = None
    subject: Optional[str] = None
    rendered_body: Optional[str] = None
    attachment_path: Optional[str] = None
    eligibility: Optional[bool] = None
    status: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    # ── Computed helpers ──

    @property
    def is_send_eligible(self) -> bool:
        """Check all eligibility conditions from AGENTS.md."""
        return (
            self.email is not None
            and self.email_verification_status == "valid"
            and self.honorific in ("Hanım", "Bey")
            and self.honorific_confidence == "high"
            and self.personalization_paragraph is not None
            and self.personalization_source_urls_json is not None
            and self.rendered_body is not None
            and self.subject == "Selam & Tanışma"
            and self.attachment_path is not None
            and Path(self.attachment_path).exists()
        )


class Campaign(BaseModel):
    id: Optional[int] = None
    name: str
    target_leads: int = 100
    snapshot_hash: Optional[str] = None
    approved: bool = False
    approved_at: Optional[str] = None
    scheduled_start: Optional[str] = None
    timezone: str = "Europe/Istanbul"
    status: str = CampaignStatus.BUILDING.value


class Send(BaseModel):
    id: Optional[int] = None
    campaign_id: int
    lead_id: int
    scheduled_at: Optional[str] = None
    attempted_at: Optional[str] = None
    sent_at: Optional[str] = None
    gmail_message_id: Optional[str] = None
    error_code: Optional[str] = None
    error_message: Optional[str] = None


# ── Config loader ─────────────────────────────────────────────────────────


class CampaignConfig(BaseModel):
    """Loads and validates config/campaign.yaml."""

    campaign_name: str
    timezone: str
    target_leads: int
    preview_count: int
    approval_required: bool
    scheduled_start: str
    send_interval_seconds: int
    max_retries_per_email: int
    followups_enabled: bool

    # Candidate
    candidate_name: str
    cv_path: str
    target_roles: list[str]

    # Company ICP
    geography: str
    max_employees: int
    sectors: list[str]
    mention_work_mode_in_email: bool

    # Scoring weights
    founder_quality_weight: float
    company_potential_weight: float
    sector_fit_weight: float
    funding_traction_weight: float

    # Email enrichment
    primary_provider: str
    fallback_provider: str
    allow_pattern_guessing: bool
    hunter_eligible_statuses: list[str]
    hunter_accept_all_enabled: bool
    hunter_minimum_score: int

    # Sending
    sending_provider: str
    require_oauth: bool
    require_attachment: bool
    attachment_path: str
    subject: str

    @classmethod
    def from_yaml(cls, path: str = "config/campaign.yaml") -> "CampaignConfig":
        """Load configuration from campaign.yaml."""
        with open(path) as f:
            raw = yaml.safe_load(f)

        c = raw["campaign"]
        cand = raw["candidate"]
        icp = raw["company_icp"]
        sw = icp["scoring_weights"]
        ee = raw["email_enrichment"]
        snd = raw["sending"]

        return cls(
            campaign_name=c["name"],
            timezone=c["timezone"],
            target_leads=c["target_leads"],
            preview_count=c["preview_count"],
            approval_required=c["approval_required"],
            scheduled_start=c["scheduled_start"],
            send_interval_seconds=c["send_interval_seconds"],
            max_retries_per_email=c["max_retries_per_email"],
            followups_enabled=c["followups_enabled"],
            candidate_name=cand["name"],
            cv_path=cand["cv_path"],
            target_roles=cand["target_roles"],
            geography=icp["geography"],
            max_employees=icp["max_employees"],
            sectors=icp["sectors"],
            mention_work_mode_in_email=icp["mention_work_mode_in_email"],
            founder_quality_weight=sw["founder_quality"],
            company_potential_weight=sw["company_potential"],
            sector_fit_weight=sw["sector_fit"],
            funding_traction_weight=sw["funding_traction"],
            primary_provider=ee["primary_provider"],
            fallback_provider=ee["fallback_provider"],
            allow_pattern_guessing=ee["allow_pattern_guessing"],
            hunter_eligible_statuses=ee["hunter"]["eligible_statuses"],
            hunter_accept_all_enabled=ee["hunter"]["accept_all_enabled"],
            hunter_minimum_score=ee["hunter"]["minimum_score"],
            sending_provider=snd["provider"],
            require_oauth=snd["require_oauth"],
            require_attachment=snd["require_attachment"],
            attachment_path=snd["attachment_path"],
            subject=snd["subject"],
        )
