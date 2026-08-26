"""Company scoring and classification logic.

Weights from config/campaign.yaml:
  founder_quality  : 35%
  company_potential : 30%
  sector_fit       : 20%
  funding_traction : 15%
"""

from __future__ import annotations

from .models import CompanyStatus


def score_company(
    founder_quality: float,
    company_potential: float,
    sector_fit: float,
    funding_traction: float,
    *,
    w_founder: float = 0.35,
    w_potential: float = 0.30,
    w_sector: float = 0.20,
    w_funding: float = 0.15,
) -> float:
    """Return weighted total fit score (0–100)."""
    total = (
        founder_quality * w_founder
        + company_potential * w_potential
        + sector_fit * w_sector
        + funding_traction * w_funding
    )
    return round(min(max(total, 0), 100), 2)


def classify_company(
    total_score: float,
    funding_status: str | None,
    *,
    outreach_threshold: float = 50.0,
    watchlist_threshold: float = 60.0,
) -> CompanyStatus:
    """Classify a company based on score and funding status.

    Rules from AGENTS.md:
    - Funded + sufficiently strong → OUTREACH
    - Unfunded but exceptionally promising (score >= watchlist_threshold) → WATCHLIST
    - Everything else → REJECT
    """
    is_funded = funding_status and funding_status.lower() not in (
        "unfunded",
        "bootstrapped",
        "none",
        "",
    )

    if is_funded and total_score >= outreach_threshold:
        return CompanyStatus.OUTREACH
    elif not is_funded and total_score >= watchlist_threshold:
        return CompanyStatus.WATCHLIST
    elif is_funded and total_score < outreach_threshold:
        return CompanyStatus.REJECT
    else:
        return CompanyStatus.REJECT
