#!/usr/bin/env python3
"""Batch ingest researched companies and leads into the SQLite database.

This script is populated by the agent's web research and run once to
seed the database. It does NOT scrape or automate external access.
"""

import json
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src import db
from src.research import ingest_company, ingest_lead

# ── Company research data ─────────────────────────────────────────────────
# Each entry is the agent's structured summary of publicly available information
# gathered via web search tools. Source URLs are recorded per research-policy.md.

COMPANIES = [
    # ── AI SECTOR ──────────────────────────────────────────────────────
    {
        "name": "Lucida AI",
        "domain": "lucida.ai",
        "website": "https://lucida.ai",
        "sector": "AI",
        "description": "Speech-native AI platform for personalized English-speaking coaching. Proprietary Speech Language Models provide real-time feedback.",
        "location": "London / Istanbul",
        "work_mode": "Hybrid",
        "employee_count": 25,
        "employee_count_confidence": "estimated",
        "funding_status": "Seed",
        "funding_details": "$8.25M total seed funding (June 2026). Investors: Velocity Capital, Next Tier Ventures, Look AI Ventures, Boğaziçi Ventures, Yapı Kredi FRWRD",
        "funding_source_url": "https://mobidictum.com",
        "founder_quality_score": 75,
        "company_potential_score": 80,
        "sector_fit_score": 85,
        "funding_traction_score": 85,
        "rationale": "Strong AI product with 3M+ users across 150 countries. Founder Mustafa Girgin previously co-founded Coensio (acquired by Kariyer.net). Well-funded seed round.",
        "founders": [
            {
                "full_name": "Mustafa Girgin",
                "title": "Co-founder & CEO",
                "university": None,
                "previous_companies": "Coensio (acquired by Kariyer.net 2022)",
                "evidence": "Serial entrepreneur, previous exit via acquisition. Co-founded Coensio HR tech startup.",
                "source_urls": ["https://mobidictum.com", "https://slator.com"]
            },
            {
                "full_name": "Mustafa Sait Demirci",
                "title": "Co-founder",
                "university": None,
                "previous_companies": None,
                "evidence": "Co-founder of Lucida AI speech platform.",
                "source_urls": ["https://slator.com"]
            }
        ]
    },
    {
        "name": "kayIQ.ai",
        "domain": "kayiq.ai",
        "website": "https://kayiq.ai",
        "sector": "AI",
        "description": "AI-powered autonomous QA and software testing platform using Agentic AI for test design, execution, and maintenance.",
        "location": "Istanbul (Ataşehir)",
        "work_mode": "Hybrid",
        "employee_count": 10,
        "employee_count_confidence": "estimated",
        "funding_status": "Seed",
        "funding_details": "$500K seed funding (Aug 2026) from founders and Magis Teknoloji",
        "funding_source_url": "https://dailysabah.com",
        "founder_quality_score": 60,
        "company_potential_score": 70,
        "sector_fit_score": 80,
        "funding_traction_score": 50,
        "rationale": "Interesting AI QA automation product. Founders have 25+ years cumulative telecom/enterprise experience. Small seed round but high-growth potential sector.",
        "founders": [
            {
                "full_name": "Tolga Özel",
                "title": "Founder & Head of Product Strategy",
                "university": None,
                "previous_companies": "AI transformation consulting",
                "evidence": "Executive technology consultant with AI transformation background.",
                "source_urls": ["https://kayiq.ai", "https://dailysabah.com"]
            },
            {
                "full_name": "Kubilay Şahhüseyinoğlu",
                "title": "Founder & Head of Customer Success",
                "university": None,
                "previous_companies": "Telecom (BSS/OSS)",
                "evidence": "Telecom transformation specialist.",
                "source_urls": ["https://kayiq.ai"]
            },
            {
                "full_name": "Işık Endir",
                "title": "Founder & Head of QA Practice",
                "university": None,
                "previous_companies": "Enterprise QA",
                "evidence": "QA strategy and test governance expert.",
                "source_urls": ["https://kayiq.ai"]
            }
        ]
    },
    {
        "name": "Novus",
        "domain": "novus.team",
        "website": "https://novus.team",
        "sector": "AI",
        "description": "LLM-based AI agent orchestration platform for enterprises. Builds agentic AI teams for workflow automation.",
        "location": "Istanbul",
        "work_mode": "Hybrid",
        "employee_count": 20,
        "employee_count_confidence": "estimated",
        "funding_status": "Seed",
        "funding_details": "$2.5M Seed (Nov 2024). Also received Yapay Zeka Fabrikası investment (Nov 2025).",
        "funding_source_url": "https://fundediq.co",
        "founder_quality_score": 70,
        "company_potential_score": 80,
        "sector_fit_score": 90,
        "funding_traction_score": 70,
        "rationale": "Strong AI agent orchestration play. Team includes Head of Growth and Head of Sales roles — signals growth-stage readiness.",
        "founders": [
            {
                "full_name": "Egehan Asad",
                "title": "Co-Founder & CEO",
                "university": None,
                "previous_companies": None,
                "evidence": "CEO leading AI agent platform.",
                "source_urls": ["https://fundediq.co"]
            },
            {
                "full_name": "Vorga Can",
                "title": "Co-Founder & CRO",
                "university": None,
                "previous_companies": None,
                "evidence": "CRO at Novus AI.",
                "source_urls": ["https://fundediq.co"]
            }
        ]
    },
    {
        "name": "Syntonym",
        "domain": "syntonym.io",
        "website": "https://syntonym.io",
        "sector": "AI",
        "description": "Generative AI for visual data anonymization. Anonymizes faces while preserving analytical metrics (age, emotion) for GDPR/KVKK compliance.",
        "location": "Istanbul",
        "work_mode": "Hybrid",
        "employee_count": 10,
        "employee_count_confidence": "estimated",
        "funding_status": "Seed",
        "funding_details": "Seed round (June 2026), amount undisclosed.",
        "funding_source_url": "https://fundediq.co",
        "founder_quality_score": 65,
        "company_potential_score": 75,
        "sector_fit_score": 80,
        "funding_traction_score": 55,
        "rationale": "Unique AI privacy product with clear regulatory tailwind (GDPR/KVKK). Small team but strong niche.",
        "founders": [
            {
                "full_name": "Batuhan Ozcan",
                "title": "Founder",
                "university": None,
                "previous_companies": None,
                "evidence": "Founder of Syntonym visual anonymization AI.",
                "source_urls": ["https://fundediq.co"]
            }
        ]
    },
    {
        "name": "Kant Labs",
        "domain": "kantlabs.ai",
        "website": "https://kantlabs.ai",
        "sector": "AI",
        "description": "AI-focused software startup in education technology.",
        "location": "Istanbul",
        "work_mode": "Remote",
        "employee_count": 5,
        "employee_count_confidence": "estimated",
        "funding_status": "Seed",
        "funding_details": "$250K seed (July 2026).",
        "funding_source_url": "https://fundediq.co",
        "founder_quality_score": 50,
        "company_potential_score": 55,
        "sector_fit_score": 70,
        "funding_traction_score": 40,
        "rationale": "Very early stage, small seed. AI education potential but limited founder evidence.",
        "founders": []
    },
    {
        "name": "IdeaSets",
        "domain": "ideasets.com",
        "website": "https://ideasets.com",
        "sector": "AI",
        "description": "AI software startup focused on idea management and innovation.",
        "location": "Istanbul",
        "work_mode": "Hybrid",
        "employee_count": 10,
        "employee_count_confidence": "estimated",
        "funding_status": "Pre-Seed",
        "funding_details": "$1.3M pre-seed (June 2026).",
        "funding_source_url": "https://fundediq.co",
        "founder_quality_score": 55,
        "company_potential_score": 65,
        "sector_fit_score": 75,
        "funding_traction_score": 55,
        "rationale": "Good pre-seed funding for AI idea management. Limited public founder info.",
        "founders": []
    },
    {
        "name": "Buluttan",
        "domain": "buluttan.com",
        "website": "https://buluttan.com",
        "sector": "AI",
        "description": "AI-based weather intelligence for energy, logistics, aviation. Turkey's first private meteorology company. Hyper-local forecasting.",
        "location": "Istanbul",
        "work_mode": "Hybrid",
        "employee_count": 30,
        "employee_count_confidence": "estimated",
        "funding_status": "Bridge",
        "funding_details": "$1M bridge investment (Dec 2025).",
        "funding_source_url": "https://fundediq.co",
        "founder_quality_score": 70,
        "company_potential_score": 75,
        "sector_fit_score": 70,
        "funding_traction_score": 65,
        "rationale": "Turkey's first private meteorology company. Strong domain expertise. Multiple co-founders with technical backgrounds.",
        "founders": [
            {
                "full_name": "Eren Kısmet",
                "title": "Co-Founder",
                "university": None,
                "previous_companies": None,
                "evidence": "Co-founder of Turkey's first private meteorology AI company.",
                "source_urls": ["https://buluttan.com"]
            },
            {
                "full_name": "Burçin Kısmet",
                "title": "Co-Founder",
                "university": None,
                "previous_companies": None,
                "evidence": "Co-founder.",
                "source_urls": ["https://buluttan.com"]
            }
        ]
    },
    {
        "name": "VenueX",
        "domain": "venuex.co",
        "website": "https://venuex.co",
        "sector": "SaaS",
        "description": "Retail marketing automation using AI agents to connect digital ad spend to physical in-store sales. Expanded to MENA (Dubai, Riyadh).",
        "location": "Istanbul",
        "work_mode": "Hybrid",
        "employee_count": 20,
        "employee_count_confidence": "estimated",
        "funding_status": "Bridge",
        "funding_details": "$1.2M bridge round (June 2025).",
        "funding_source_url": "https://fundediq.co",
        "founder_quality_score": 65,
        "company_potential_score": 75,
        "sector_fit_score": 85,
        "funding_traction_score": 65,
        "rationale": "SaaS marketing automation with AI agents. International expansion to MENA shows traction.",
        "founders": [
            {
                "full_name": "Kursad Arman",
                "title": "Co-Founder & CEO",
                "university": None,
                "previous_companies": None,
                "evidence": "CEO of VenueX, retail marketing AI platform.",
                "source_urls": ["https://venuex.co"]
            }
        ]
    },
    {
        "name": "Co-One",
        "domain": "co-one.co",
        "website": "https://co-one.co",
        "sector": "AI",
        "description": "Real-world ready AI agents and data infrastructure for e-commerce and banking. Operations in Turkey, MENA, Western Europe.",
        "location": "Istanbul / Estonia",
        "work_mode": "Hybrid",
        "employee_count": 15,
        "employee_count_confidence": "estimated",
        "funding_status": "Pre-Series A",
        "funding_details": "€1M Pre-Series A (May 2025).",
        "funding_source_url": "https://fundediq.co",
        "founder_quality_score": 60,
        "company_potential_score": 70,
        "sector_fit_score": 80,
        "funding_traction_score": 60,
        "rationale": "AI agents for e-commerce/banking. Multi-market presence. European funding.",
        "founders": [
            {
                "full_name": "Arman Kayhan",
                "title": "Co-Founder",
                "university": None,
                "previous_companies": None,
                "evidence": "Co-founder of Co-One AI agents platform.",
                "source_urls": ["https://co-one.co"]
            },
            {
                "full_name": "Mert Menekşe",
                "title": "Co-Founder",
                "university": None,
                "previous_companies": None,
                "evidence": "Co-founder.",
                "source_urls": ["https://co-one.co"]
            }
        ]
    },
    # ── GAMING SECTOR ──────────────────────────────────────────────────
    {
        "name": "SuperGears Games",
        "domain": "supergears.games",
        "website": "https://supergears.games",
        "sector": "Gaming",
        "description": "Mobile racing game studio. Flagship: Racing Kingdom — millions of players, awarded Best Mobile Game & Best Racing Game at 2025 Kristal Piksel.",
        "location": "Istanbul (Yıldız Technical University Technopark)",
        "work_mode": "Hybrid",
        "employee_count": 25,
        "employee_count_confidence": "estimated",
        "funding_status": "Seed",
        "funding_details": "$2.1M seed (Nov 2025), led by Hedef Portföy, APY Ventures, KRAFTON. Total raised: $3.6M+ including $1.5M pre-seed (2023).",
        "funding_source_url": "https://gamespress.com",
        "founder_quality_score": 75,
        "company_potential_score": 80,
        "sector_fit_score": 90,
        "funding_traction_score": 75,
        "rationale": "Veteran gaming founders (20+ yrs experience, ZULA/Kabus22). Award-winning Racing Kingdom. KRAFTON as strategic investor.",
        "founders": [
            {
                "full_name": "Yasin Demirden",
                "title": "Co-Founder",
                "university": None,
                "previous_companies": "Kabus 22, SüperCan, ZULA, ZULA BR",
                "evidence": "20+ years gaming experience. Created multiple successful Turkish gaming IPs.",
                "source_urls": ["https://supergears.games", "https://egirisim.com"]
            },
            {
                "full_name": "Yakup Demirden",
                "title": "Co-Founder",
                "university": None,
                "previous_companies": "Kabus 22, SüperCan, ZULA, ZULA BR",
                "evidence": "20+ years gaming experience alongside brother Yasin.",
                "source_urls": ["https://supergears.games", "https://egirisim.com"]
            }
        ]
    },
    {
        "name": "Bold Games",
        "domain": "boldgames.co",
        "website": "https://boldgames.co",
        "sector": "Gaming",
        "description": "Casual mobile gaming studio, debut title: Market Match (sort-puzzle genre). Team of ~10 in Istanbul.",
        "location": "Istanbul",
        "work_mode": "On-site",
        "employee_count": 10,
        "employee_count_confidence": "reported",
        "funding_status": "Seed",
        "funding_details": "$6M seed (July 2026), led by Arcadia Gaming Partners, Makers Fund, e2vc. Angels + JIMCO.",
        "funding_source_url": "https://pocketgamer.biz",
        "founder_quality_score": 80,
        "company_potential_score": 75,
        "sector_fit_score": 90,
        "funding_traction_score": 80,
        "rationale": "Strong founder team from Bigger Games, Dream Games, Agave, ZeptoLab, Rollic. Large seed for a 10-person team.",
        "founders": [
            {
                "full_name": "Ulaş Mergen",
                "title": "CEO & Founder",
                "university": None,
                "previous_companies": "Bigger Games, Dream Games, Agave Games, ZeptoLab, Rollic",
                "evidence": "Extensive gaming leadership background across top Turkish studios.",
                "source_urls": ["https://pocketgamer.biz", "https://arabfounders.net"]
            },
            {
                "full_name": "Atakan Tuğlu",
                "title": "CMO & Co-Founder",
                "university": None,
                "previous_companies": "Turkish gaming industry",
                "evidence": "CMO with gaming marketing experience.",
                "source_urls": ["https://pocketgamer.biz"]
            }
        ]
    },
    {
        "name": "Circle Games",
        "domain": "circlegames.co",
        "website": "https://circlegames.co",
        "sector": "Gaming",
        "description": "Casual mobile puzzle studio. Debut title: Sort Express! Founded by university friends from Gram Games, Dream Games, Good Job Games.",
        "location": "Istanbul",
        "work_mode": "Hybrid",
        "employee_count": 15,
        "employee_count_confidence": "estimated",
        "funding_status": "Seed",
        "funding_details": "$7.25M seed (July 2025), led by BITKRAFT Ventures. Also: a16z Speedrun, Play Ventures, e2vc, APY Ventures.",
        "funding_source_url": "https://mobidictum.com",
        "founder_quality_score": 85,
        "company_potential_score": 80,
        "sector_fit_score": 90,
        "funding_traction_score": 85,
        "rationale": "Founders met at university, worked at Gram Games (acquired by Zynga), Dream Games, Good Job Games. a16z backing. Strong pedigree.",
        "founders": [
            {
                "full_name": "Göktürk Balıkçı",
                "title": "CEO & Co-Founder",
                "university": None,
                "previous_companies": "Gram Games, Dream Games, Good Job Games",
                "evidence": "Met co-founders at university. Led teams at top Turkish gaming companies.",
                "source_urls": ["https://a16z.com", "https://mobidictum.com"]
            },
            {
                "full_name": "Mustafa Özdemir",
                "title": "CPO & Co-Founder",
                "university": None,
                "previous_companies": "Gram Games, Dream Games",
                "evidence": "Product leader from leading Turkish gaming studios.",
                "source_urls": ["https://bitkraft.vc", "https://mobidictum.com"]
            }
        ]
    },
    {
        "name": "Fuse Games",
        "domain": "fusegames.co",
        "website": "https://fusegames.co",
        "sector": "Gaming",
        "description": "Mobile gaming studio focused on original IP development. Proprietary tools and technology.",
        "location": "Istanbul",
        "work_mode": "On-site",
        "employee_count": 20,
        "employee_count_confidence": "estimated",
        "funding_status": "Series A",
        "funding_details": "$7M (May 2025), led by Griffin Gaming Partners. Also: Lakestar, NFX Capital, Actera. Previous: $2M seed (June 2023).",
        "funding_source_url": "https://finsmes.com",
        "founder_quality_score": 70,
        "company_potential_score": 75,
        "sector_fit_score": 85,
        "funding_traction_score": 75,
        "rationale": "Strong investor lineup (Griffin Gaming, Lakestar, NFX). Focus on original IP development.",
        "founders": [
            {
                "full_name": "Akın Semih Şahan",
                "title": "CEO & Co-Founder",
                "university": None,
                "previous_companies": None,
                "evidence": "CEO leading original IP mobile gaming studio.",
                "source_urls": ["https://webrazzi.com", "https://finsmes.com"]
            }
        ]
    },
    {
        "name": "Bigger Games",
        "domain": "biggergames.com",
        "website": "https://biggergames.com",
        "sector": "Gaming",
        "description": "Casual puzzle mobile games (Kitchen Masters). Data-driven product development. Founded by Peak Games alumni.",
        "location": "Istanbul (Şişli)",
        "work_mode": "On-site",
        "employee_count": 40,
        "employee_count_confidence": "estimated",
        "funding_status": "Series A",
        "funding_details": "$25M Series A (June 2025), led by Goodwater Capital. Previous: $6M seed (2020, Index Ventures).",
        "funding_source_url": "https://webrazzi.com",
        "founder_quality_score": 85,
        "company_potential_score": 85,
        "sector_fit_score": 90,
        "funding_traction_score": 90,
        "rationale": "Peak Games alumni (Zynga $1.8B acquisition). Top-tier investors: Goodwater, Index Ventures, Play Ventures. Strong traction.",
        "founders": [
            {
                "full_name": "Hakan Ulvan",
                "title": "CEO & Co-Founder",
                "university": None,
                "previous_companies": "Peak Games (acquired by Zynga for $1.8B)",
                "evidence": "Led teams at Peak Games before its landmark $1.8B acquisition.",
                "source_urls": ["https://indexventures.com", "https://gamizm.com"]
            },
            {
                "full_name": "Erkan Gürel",
                "title": "Co-Founder",
                "university": None,
                "previous_companies": "Peak Games",
                "evidence": "Peak Games alumni.",
                "source_urls": ["https://gamizm.com"]
            }
        ]
    },
    {
        "name": "Agave Games",
        "domain": "agavegames.com",
        "website": "https://agavegames.com",
        "sector": "Gaming",
        "description": "Casual puzzle mobile games (Find the Cat). Strong traction.",
        "location": "Istanbul",
        "work_mode": "Hybrid",
        "employee_count": 44,
        "employee_count_confidence": "estimated",
        "funding_status": "Series A",
        "funding_details": "$25M total: $7M seed (2022), $18M Series A (Dec 2024).",
        "funding_source_url": "https://fundediq.co",
        "founder_quality_score": 75,
        "company_potential_score": 80,
        "sector_fit_score": 90,
        "funding_traction_score": 85,
        "rationale": "Strong Series A funding. Successful Find the Cat game. Growing team.",
        "founders": [
            {
                "full_name": "Alper Oner",
                "title": "CEO",
                "university": None,
                "previous_companies": None,
                "evidence": "CEO of Agave Games.",
                "source_urls": ["https://fundediq.co"]
            }
        ]
    },
    # ── SaaS SECTOR ────────────────────────────────────────────────────
    {
        "name": "Wask",
        "domain": "wask.co",
        "website": "https://wask.co",
        "sector": "SaaS",
        "description": "AI-powered digital marketing platform for automated ad management across Google, Facebook, Instagram.",
        "location": "Istanbul",
        "work_mode": "Hybrid",
        "employee_count": 30,
        "employee_count_confidence": "estimated",
        "funding_status": "Seed",
        "funding_details": "Funded 2023-2024, amount not publicly disclosed.",
        "funding_source_url": "https://startups.watch",
        "founder_quality_score": 60,
        "company_potential_score": 70,
        "sector_fit_score": 85,
        "funding_traction_score": 60,
        "rationale": "AI-driven marketing SaaS. Good sector fit for Growth/Product roles.",
        "founders": []
    },
]


def main():
    """Ingest all researched companies and their founders into the database."""
    db.init_db()
    conn = db.get_connection()

    print(f"\n{'='*60}")
    print(f"BATCH INGESTION: {len(COMPANIES)} companies")
    print(f"{'='*60}\n")

    stats = {"OUTREACH": 0, "WATCHLIST": 0, "REJECT": 0}

    for company_data in COMPANIES:
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
    print(f"SUMMARY: OUTREACH={stats.get('OUTREACH',0)}  WATCHLIST={stats.get('WATCHLIST',0)}  REJECT={stats.get('REJECT',0)}")
    print(f"{'='*60}\n")

    conn.close()


if __name__ == "__main__":
    main()
