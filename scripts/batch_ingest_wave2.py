#!/usr/bin/env python3
"""Batch ingest ADDITIONAL researched companies (wave 2)."""

import json
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src import db
from src.research import ingest_company

COMPANIES_WAVE2 = [
    # ── AI SECTOR ──────────────────────────────────────────────────────
    {
        "name": "Cypien AI",
        "domain": "cypien.ai",
        "website": "https://cypien.ai",
        "sector": "AI",
        "description": "AI-powered digital experience / Generative Commerce platform.",
        "location": "Istanbul (Sarıyer)",
        "work_mode": "Hybrid",
        "employee_count": 8,
        "employee_count_confidence": "estimated",
        "funding_status": "Pre-Seed",
        "funding_details": "$300K pre-seed (Jan 2026, $3M valuation), follow-on (June 2026, $4.5M valuation).",
        "funding_source_url": "https://fundediq.co",
        "founder_quality_score": 55,
        "company_potential_score": 65,
        "sector_fit_score": 80,
        "funding_traction_score": 50,
        "rationale": "Early-stage AI generative commerce. Growing valuation (3M → 4.5M in 5 months).",
        "founders": []
    },
    {
        "name": "Kynic Agent",
        "domain": "kynicagent.com",
        "website": "https://kynicagent.com",
        "sector": "AI",
        "description": "AI agent startup. Seed funding received June 2026.",
        "location": "Istanbul",
        "work_mode": "Remote",
        "employee_count": 5,
        "employee_count_confidence": "estimated",
        "funding_status": "Seed",
        "funding_details": "Seed round (June 2026), amount undisclosed.",
        "funding_source_url": "https://fundediq.co",
        "founder_quality_score": 50,
        "company_potential_score": 60,
        "sector_fit_score": 80,
        "funding_traction_score": 45,
        "rationale": "AI agent startup, very early stage. Limited public info on founders.",
        "founders": []
    },
    {
        "name": "CBOT",
        "domain": "cbot.ai",
        "website": "https://cbot.ai",
        "sector": "AI",
        "description": "AI-powered conversational platform. Enterprise chatbots and virtual assistants using NLU/NLP technology.",
        "location": "Istanbul",
        "work_mode": "Hybrid",
        "employee_count": 40,
        "employee_count_confidence": "estimated",
        "funding_status": "Series A",
        "funding_details": "Multiple rounds. Series A funded.",
        "funding_source_url": "https://startups.watch",
        "founder_quality_score": 70,
        "company_potential_score": 75,
        "sector_fit_score": 85,
        "funding_traction_score": 70,
        "rationale": "Leading Turkish conversational AI. Enterprise clients. Growing team but still ≤50.",
        "founders": []
    },
    {
        "name": "B2Metric",
        "domain": "b2metric.com",
        "website": "https://b2metric.com",
        "sector": "AI",
        "description": "AI-driven predictive analytics and customer intelligence platform. AutoML for business insights.",
        "location": "Istanbul",
        "work_mode": "Hybrid",
        "employee_count": 20,
        "employee_count_confidence": "estimated",
        "funding_status": "Seed",
        "funding_details": "Seed funded.",
        "funding_source_url": "https://startups.watch",
        "founder_quality_score": 60,
        "company_potential_score": 70,
        "sector_fit_score": 85,
        "funding_traction_score": 60,
        "rationale": "AI analytics SaaS. AutoML approach is differentiated. Good sector fit.",
        "founders": []
    },
    {
        "name": "Vispera",
        "domain": "vispera.co",
        "website": "https://vispera.co",
        "sector": "AI",
        "description": "AI-powered image recognition for retail execution. Computer vision for shelf analytics and in-store optimization.",
        "location": "Istanbul",
        "work_mode": "Hybrid",
        "employee_count": 45,
        "employee_count_confidence": "estimated",
        "funding_status": "Series A",
        "funding_details": "Multiple rounds including Series A.",
        "funding_source_url": "https://startups.watch",
        "founder_quality_score": 75,
        "company_potential_score": 80,
        "sector_fit_score": 85,
        "funding_traction_score": 75,
        "rationale": "Leading retail AI company. Strong tech (computer vision). International clients.",
        "founders": []
    },
    {
        "name": "OctoXLabs",
        "domain": "octoxlabs.com",
        "website": "https://octoxlabs.com",
        "sector": "AI",
        "description": "AI-driven cyber asset attack security management (CAASM) platform.",
        "location": "Istanbul",
        "work_mode": "Hybrid",
        "employee_count": 15,
        "employee_count_confidence": "estimated",
        "funding_status": "Seed",
        "funding_details": "Investment from Yapı Kredi FRWRD GSYF (June 2025).",
        "funding_source_url": "https://startups.watch",
        "founder_quality_score": 60,
        "company_potential_score": 70,
        "sector_fit_score": 80,
        "funding_traction_score": 60,
        "rationale": "Cybersecurity AI. Backed by Yapı Kredi FRWRD. Growing CAASM market.",
        "founders": []
    },
    # ── SaaS SECTOR ────────────────────────────────────────────────────
    {
        "name": "Storyly",
        "domain": "storyly.io",
        "website": "https://storyly.io",
        "sector": "SaaS",
        "description": "Mobile engagement platform through interactive stories and shoppable content for apps.",
        "location": "Istanbul",
        "work_mode": "Hybrid",
        "employee_count": 45,
        "employee_count_confidence": "estimated",
        "funding_status": "Series A",
        "funding_details": "Series A funded. Multiple investment rounds.",
        "funding_source_url": "https://startups.watch",
        "founder_quality_score": 70,
        "company_potential_score": 80,
        "sector_fit_score": 85,
        "funding_traction_score": 75,
        "rationale": "Strong SaaS engagement product. International client base. Good product-market fit.",
        "founders": []
    },
    {
        "name": "Segmentify",
        "domain": "segmentify.com",
        "website": "https://segmentify.com",
        "sector": "SaaS",
        "description": "AI-powered e-commerce personalization and analytics platform. Real-time product recommendations.",
        "location": "Istanbul",
        "work_mode": "Hybrid",
        "employee_count": 35,
        "employee_count_confidence": "estimated",
        "funding_status": "Series A",
        "funding_details": "Series A funded.",
        "funding_source_url": "https://startups.watch",
        "founder_quality_score": 65,
        "company_potential_score": 75,
        "sector_fit_score": 85,
        "funding_traction_score": 70,
        "rationale": "E-commerce personalization SaaS. AI-driven recommendations. International expansion.",
        "founders": []
    },
    {
        "name": "TeamSec",
        "domain": "teamsec.com",
        "website": "https://teamsec.com",
        "sector": "SaaS",
        "description": "AI-powered Securitization-as-a-Service for financial institutions. Cloud-based regtech.",
        "location": "Istanbul",
        "work_mode": "Hybrid",
        "employee_count": 20,
        "employee_count_confidence": "estimated",
        "funding_status": "Seed",
        "funding_details": "$7.6M (Feb 2025), co-led by Deniz Ventures and Rasmal Ventures.",
        "funding_source_url": "https://fundediq.co",
        "founder_quality_score": 65,
        "company_potential_score": 70,
        "sector_fit_score": 70,
        "funding_traction_score": 75,
        "rationale": "Well-funded fintech SaaS. AI-powered securitization is a high-value niche.",
        "founders": []
    },
    {
        "name": "ThingsHappen",
        "domain": "thingshappen.co",
        "website": "https://thingshappen.co",
        "sector": "AI",
        "description": "AI-based InsurTech platform. Founded Sept 2024.",
        "location": "Istanbul",
        "work_mode": "Hybrid",
        "employee_count": 8,
        "employee_count_confidence": "estimated",
        "funding_status": "Pre-Seed",
        "funding_details": "Investment at $2M valuation (Aug 2025), led by ŞirketOrtağım Angel Network.",
        "funding_source_url": "https://fundediq.co",
        "founder_quality_score": 55,
        "company_potential_score": 60,
        "sector_fit_score": 70,
        "funding_traction_score": 50,
        "rationale": "Early-stage AI InsurTech. Small angel round.",
        "founders": []
    },
    # ── GAMING SECTOR ──────────────────────────────────────────────────
    {
        "name": "Grand Games",
        "domain": "grandgames.co",
        "website": "https://grandgames.co",
        "sector": "Gaming",
        "description": "Mobile gaming studio — Magic Sort!, Car Match. Rapid scaling: $30M Series A just 9 months after pre-seed. ~14 person team.",
        "location": "Istanbul",
        "work_mode": "On-site",
        "employee_count": 14,
        "employee_count_confidence": "reported",
        "funding_status": "Series A",
        "funding_details": "$30M Series A (2025, led by Balderton). Total raised: $105M by mid-2026.",
        "funding_source_url": "https://mobidictum.com",
        "founder_quality_score": 80,
        "company_potential_score": 90,
        "sector_fit_score": 90,
        "funding_traction_score": 95,
        "rationale": "Exceptional growth trajectory. $105M raised with ~14 people. Balderton-led. Top-tier gaming traction.",
        "founders": [
            {
                "full_name": "Bekir Batuhan Çelebi",
                "title": "Co-Founder",
                "university": None,
                "previous_companies": None,
                "evidence": "Co-founder of Grand Games which raised $105M total.",
                "source_urls": ["https://mobidictum.com"]
            },
            {
                "full_name": "Mehmet Çalım",
                "title": "Co-Founder",
                "university": None,
                "previous_companies": None,
                "evidence": "Co-founder.",
                "source_urls": ["https://mobidictum.com"]
            }
        ]
    },
    {
        "name": "Flow Games",
        "domain": "flowgames.co",
        "website": "https://flowgames.co",
        "sector": "Gaming",
        "description": "Mobile gaming studio founded July 2025 by veterans from Peak, Fomo Games, Good Job Games, Dream Games. Debut: Smash Fest.",
        "location": "Istanbul",
        "work_mode": "On-site",
        "employee_count": 10,
        "employee_count_confidence": "estimated",
        "funding_status": "Pre-Seed",
        "funding_details": "Backed by Ludus Ventures (2025).",
        "funding_source_url": "https://substack.com",
        "founder_quality_score": 80,
        "company_potential_score": 75,
        "sector_fit_score": 90,
        "funding_traction_score": 60,
        "rationale": "Peak/Dream Games/Good Job Games alumni. Ludus Ventures backing. Very early but strong pedigree.",
        "founders": []
    },
]


def main():
    db.init_db()
    conn = db.get_connection()

    print(f"\n{'='*60}")
    print(f"BATCH INGESTION WAVE 2: {len(COMPANIES_WAVE2)} companies")
    print(f"{'='*60}\n")

    stats = {"OUTREACH": 0, "WATCHLIST": 0, "REJECT": 0}

    for company_data in COMPANIES_WAVE2:
        founders = company_data.pop("founders", [])
        result = ingest_company(conn, founders=founders, **company_data)

        classification = result["classification"]
        stats[classification] = stats.get(classification, 0) + 1

        print(
            f"  [{classification:>10}] {company_data['name']:30s} "
            f"score={result['total_fit_score']:.1f}  "
            f"({company_data.get('funding_status', 'N/A')})"
        )

    print(f"\n{'='*60}")
    print(f"WAVE 2 SUMMARY: OUTREACH={stats.get('OUTREACH',0)}  WATCHLIST={stats.get('WATCHLIST',0)}  REJECT={stats.get('REJECT',0)}")
    
    # Total count
    all_companies = db.get_all_companies(conn)
    outreach = [c for c in all_companies if c["classification"] == "OUTREACH"]
    print(f"TOTAL COMPANIES: {len(all_companies)} ({len(outreach)} OUTREACH)")
    print(f"{'='*60}\n")

    conn.close()


if __name__ == "__main__":
    main()
