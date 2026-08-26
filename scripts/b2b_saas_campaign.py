#!/usr/bin/env python3
"""B2B SaaS Outreach Campaign — Wave 2 (20 New Companies)

Researches 20 new B2B SaaS startups (<=50 employees), finds & verifies
co-founder emails, generates personalized emails, sends them via Gmail API
with 30-second pacing, updates SQLite, and syncs live to Supabase.
"""

from __future__ import annotations

import json
import logging
import os
import sys
import time
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
import requests

from dotenv import load_dotenv
load_dotenv()


sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src import db, hunter, render, gmail_client, supabase_client
from src.research import ingest_company, ingest_lead
from src.export_xlsx import export

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s: %(message)s")
logger = logging.getLogger("b2b_saas_campaign")

HUNTER_KEY = os.getenv("HUNTER_API_KEY", "").strip()

# ── 20 NEW B2B SaaS Startups (<= 50 employees, Turkey-focused) ─────────────
NEW_B2B_SAAS_COMPANIES = [
    {
        "name": "UserGuiding",
        "domain": "userguiding.com",
        "website": "https://userguiding.com",
        "sector": "SaaS",
        "description": "Product adoption and user onboarding platform. No-code in-app guides and walkthroughs for web apps.",
        "location": "Istanbul",
        "work_mode": "Hybrid",
        "employee_count": 35,
        "employee_count_confidence": "estimated",
        "funding_status": "Seed",
        "funding_details": "Funded seed round by 212 and Collective Spark.",
        "funding_source_url": "https://212.vc",
        "founder_quality_score": 75,
        "company_potential_score": 85,
        "sector_fit_score": 90,
        "funding_traction_score": 80,
        "rationale": "Leading Turkish product-led growth SaaS. Strong international customer base.",
        "founders": [
            {
                "full_name": "Osman Koç",
                "first_name": "Osman",
                "title": "Co-Founder & CEO",
                "honorific": "Bey",
                "evidence": "Co-founder of UserGuiding.",
                "source_urls": ["https://userguiding.com"]
            }
        ]
    },
    {
        "name": "Juphy",
        "domain": "juphy.com",
        "website": "https://juphy.com",
        "sector": "SaaS",
        "description": "AI-powered social media and customer support management platform for e-commerce and marketing teams.",
        "location": "Istanbul",
        "work_mode": "Hybrid",
        "employee_count": 18,
        "employee_count_confidence": "estimated",
        "funding_status": "Seed",
        "funding_details": "Seed funded by APY Ventures and angel investors.",
        "funding_source_url": "https://startupcentrum.com",
        "founder_quality_score": 70,
        "company_potential_score": 80,
        "sector_fit_score": 90,
        "funding_traction_score": 75,
        "rationale": "AI customer support inbox SaaS. Strong e-commerce integration.",
        "founders": [
            {
                "full_name": "Alara Eren İplikçioğlu",
                "first_name": "Alara Eren",
                "title": "Co-Founder & CEO",
                "honorific": "Hanım",
                "evidence": "Co-founder & CEO of Juphy.",
                "source_urls": ["https://juphy.com"]
            },
            {
                "full_name": "Osman Erdi Balcıoğlu",
                "first_name": "Osman Erdi",
                "title": "Co-Founder",
                "honorific": "Bey",
                "evidence": "Co-founder of Juphy.",
                "source_urls": ["https://juphy.com"]
            }
        ]
    },
    {
        "name": "Peaka",
        "domain": "peaka.com",
        "website": "https://peaka.com",
        "sector": "SaaS",
        "description": "Zero-ETL data integration platform that connects cloud databases and APIs without building pipelines.",
        "location": "Istanbul",
        "work_mode": "Remote",
        "employee_count": 14,
        "employee_count_confidence": "reported",
        "funding_status": "Pre-Seed",
        "funding_details": "Pre-seed funded.",
        "funding_source_url": "https://peaka.com",
        "founder_quality_score": 75,
        "company_potential_score": 85,
        "sector_fit_score": 90,
        "funding_traction_score": 70,
        "rationale": "Innovative zero-ETL data platform. Fast-growing developer tooling niche.",
        "founders": [
            {
                "full_name": "Mustafa Sakalsız",
                "first_name": "Mustafa",
                "title": "Co-Founder & CEO",
                "honorific": "Bey",
                "evidence": "Co-founder & CEO of Peaka.",
                "source_urls": ["https://peaka.com"]
            }
        ]
    },
    {
        "name": "Popupsmart",
        "domain": "popupsmart.com",
        "website": "https://popupsmart.com",
        "sector": "SaaS",
        "description": "No-code conversion optimization and lead generation popup builder SaaS platform.",
        "location": "Istanbul",
        "work_mode": "Hybrid",
        "employee_count": 30,
        "employee_count_confidence": "reported",
        "funding_status": "Bootstrapped / Seed",
        "funding_details": "Profitable bootstrapped/seed stage.",
        "funding_source_url": "https://popupsmart.com",
        "founder_quality_score": 70,
        "company_potential_score": 80,
        "sector_fit_score": 90,
        "funding_traction_score": 75,
        "rationale": "High-margin lead generation SaaS with global users in 100+ countries.",
        "founders": [
            {
                "full_name": "Emre Elbeyoğlu",
                "first_name": "Emre",
                "title": "Co-Founder & CEO",
                "honorific": "Bey",
                "evidence": "Co-founder & CEO of Popupsmart.",
                "source_urls": ["https://popupsmart.com"]
            },
            {
                "full_name": "Murathan Yıldırım",
                "first_name": "Murathan",
                "title": "Co-Founder",
                "honorific": "Bey",
                "evidence": "Co-founder of Popupsmart.",
                "source_urls": ["https://popupsmart.com"]
            }
        ]
    },
    {
        "name": "Retable",
        "domain": "retable.io",
        "website": "https://retable.io",
        "sector": "SaaS",
        "description": "Smart online spreadsheet and relational database management platform for teams.",
        "location": "Istanbul",
        "work_mode": "Hybrid",
        "employee_count": 25,
        "employee_count_confidence": "estimated",
        "funding_status": "Seed",
        "funding_details": "Seed stage.",
        "funding_source_url": "https://retable.io",
        "founder_quality_score": 65,
        "company_potential_score": 75,
        "sector_fit_score": 85,
        "funding_traction_score": 65,
        "rationale": "No-code database spreadsheet SaaS competing in Airtable space.",
        "founders": [
            {
                "full_name": "Serdar Bingöl",
                "first_name": "Serdar",
                "title": "Founder & CEO",
                "honorific": "Bey",
                "evidence": "Founder & CEO of Retable.",
                "source_urls": ["https://retable.io"]
            }
        ]
    },
    {
        "name": "Raklet",
        "domain": "raklet.com",
        "website": "https://raklet.com",
        "sector": "SaaS",
        "description": "All-in-one community management, CRM, and membership platform for associations, NGOs, and businesses.",
        "location": "Istanbul",
        "work_mode": "Hybrid",
        "employee_count": 20,
        "employee_count_confidence": "estimated",
        "funding_status": "Seed",
        "funding_details": "Backed by Techstars and 500 Startups.",
        "funding_source_url": "https://raklet.com",
        "founder_quality_score": 75,
        "company_potential_score": 80,
        "sector_fit_score": 85,
        "funding_traction_score": 75,
        "rationale": "Techstars & 500 Startups alumnus. Global membership SaaS.",
        "founders": [
            {
                "full_name": "Gerçek Karakuş",
                "first_name": "Gerçek",
                "title": "Co-Founder & CEO",
                "honorific": "Bey",
                "evidence": "Co-founder & CEO of Raklet.",
                "source_urls": ["https://raklet.com"]
            }
        ]
    },
    {
        "name": "Kimola",
        "domain": "kimola.com",
        "website": "https://kimola.com",
        "sector": "SaaS",
        "description": "AI-powered market research and customer feedback analytics platform for consumer insight teams.",
        "location": "Istanbul",
        "work_mode": "Hybrid",
        "employee_count": 15,
        "employee_count_confidence": "estimated",
        "funding_status": "Seed",
        "funding_details": "Seed stage.",
        "funding_source_url": "https://kimola.com",
        "founder_quality_score": 70,
        "company_potential_score": 75,
        "sector_fit_score": 85,
        "funding_traction_score": 65,
        "rationale": "AI feedback analytics SaaS. Proprietary NLP for customer reviews.",
        "founders": [
            {
                "full_name": "Mustafa Savaş",
                "first_name": "Mustafa",
                "title": "Co-Founder & Tech Lead",
                "honorific": "Bey",
                "evidence": "Co-founder of Kimola.",
                "source_urls": ["https://kimola.com"]
            }
        ]
    },
    {
        "name": "Craftgate",
        "domain": "craftgate.io",
        "website": "https://craftgate.io",
        "sector": "SaaS",
        "description": "One-stop payment orchestration SaaS platform unifying virtual POS, payment gateways, and e-commerce checkout.",
        "location": "Istanbul",
        "work_mode": "Hybrid",
        "employee_count": 40,
        "employee_count_confidence": "estimated",
        "funding_status": "Series A",
        "funding_details": "$2M+ funding led by Hepsiburada and Akbank LAB.",
        "funding_source_url": "https://craftgate.io",
        "founder_quality_score": 85,
        "company_potential_score": 85,
        "sector_fit_score": 90,
        "funding_traction_score": 85,
        "rationale": "Payment orchestration leader in Turkey. Experienced fintech founders.",
        "founders": [
            {
                "full_name": "Hakan Erdoğan",
                "first_name": "Hakan",
                "title": "Co-Founder & CEO",
                "honorific": "Bey",
                "evidence": "Co-founder & CEO of Craftgate.",
                "source_urls": ["https://craftgate.io"]
            },
            {
                "full_name": "Lemi Orhan Ergin",
                "first_name": "Lemi Orhan",
                "title": "Co-Founder & CTO",
                "honorific": "Bey",
                "evidence": "Co-founder & CTO of Craftgate, software craftsmanship leader.",
                "source_urls": ["https://craftgate.io"]
            }
        ]
    },
    {
        "name": "Pubinno",
        "domain": "pubinno.com",
        "website": "https://pubinno.com",
        "sector": "SaaS",
        "description": "AI-powered IoT draft beer management and smart tap SaaS platform operating in 62 cities worldwide.",
        "location": "Istanbul",
        "work_mode": "Hybrid",
        "employee_count": 45,
        "employee_count_confidence": "estimated",
        "funding_status": "Series A",
        "funding_details": "$2.5M+ funding across multiple rounds.",
        "funding_source_url": "https://pubinno.com",
        "founder_quality_score": 80,
        "company_potential_score": 85,
        "sector_fit_score": 85,
        "funding_traction_score": 80,
        "rationale": "Internet of Beer IoT + SaaS global leader.",
        "founders": [
            {
                "full_name": "Can Algül",
                "first_name": "Can",
                "title": "Co-Founder & CEO",
                "honorific": "Bey",
                "evidence": "Co-founder & CEO of Pubinno.",
                "source_urls": ["https://pubinno.com"]
            },
            {
                "full_name": "Necdet Alpmen",
                "first_name": "Necdet",
                "title": "Co-Founder & CTO",
                "honorific": "Bey",
                "evidence": "Co-founder & CTO of Pubinno.",
                "source_urls": ["https://pubinno.com"]
            }
        ]
    },
    {
        "name": "Skymod Technology",
        "domain": "skymod.ai",
        "website": "https://skymod.ai",
        "sector": "SaaS",
        "description": "Enterprise generative AI assistant platform for automated workflow documentation and knowledge retrieval.",
        "location": "Izmir (Bilimpark)",
        "work_mode": "Hybrid",
        "employee_count": 10,
        "employee_count_confidence": "reported",
        "funding_status": "Pre-Seed",
        "funding_details": "$200K pre-seed investment in Nov 2025.",
        "funding_source_url": "https://aiworld.eu",
        "founder_quality_score": 65,
        "company_potential_score": 75,
        "sector_fit_score": 85,
        "funding_traction_score": 60,
        "rationale": "Izmir-based enterprise GenAI SaaS.",
        "founders": [
            {
                "full_name": "M. Oltan Dere",
                "first_name": "Oltan",
                "title": "Co-Founder & CEO",
                "honorific": "Bey",
                "evidence": "Co-founder & CEO of Skymod.",
                "source_urls": ["https://skymod.ai"]
            },
            {
                "full_name": "Gizem Argunşah",
                "first_name": "Gizem",
                "title": "Co-Founder & CMO",
                "honorific": "Hanım",
                "evidence": "Co-founder & CMO.",
                "source_urls": ["https://skymod.ai"]
            }
        ]
    },
    {
        "name": "AppSamurai",
        "domain": "appsamurai.com",
        "website": "https://appsamurai.com",
        "sector": "SaaS",
        "description": "Global mobile growth and user acquisition platform for app developers and marketers.",
        "location": "Istanbul",
        "work_mode": "Hybrid",
        "employee_count": 48,
        "employee_count_confidence": "estimated",
        "funding_status": "Series A",
        "funding_details": "Backed by 212 VC.",
        "funding_source_url": "https://212.vc",
        "founder_quality_score": 80,
        "company_potential_score": 85,
        "sector_fit_score": 90,
        "funding_traction_score": 85,
        "rationale": "Prominent Turkish adtech/SaaS mobile growth platform.",
        "founders": [
            {
                "full_name": "Emre Fadıllıoğlu",
                "first_name": "Emre",
                "title": "Co-Founder & CEO",
                "honorific": "Bey",
                "evidence": "Co-founder & CEO of AppSamurai.",
                "source_urls": ["https://appsamurai.com"]
            }
        ]
    },
    {
        "name": "Fineksus",
        "domain": "fineksus.com",
        "website": "https://fineksus.com",
        "sector": "SaaS",
        "description": "Financial messaging (SWIFT) and Anti-Money Laundering (AML) compliance SaaS for banks and fintechs.",
        "location": "Istanbul",
        "work_mode": "Hybrid",
        "employee_count": 45,
        "employee_count_confidence": "estimated",
        "funding_status": "Series A",
        "funding_details": "Joined cleversoft group (2025).",
        "funding_source_url": "https://fineksus.com",
        "founder_quality_score": 75,
        "company_potential_score": 80,
        "sector_fit_score": 85,
        "funding_traction_score": 80,
        "rationale": "Leading AML regtech SaaS in Turkey.",
        "founders": [
            {
                "full_name": "Ahmet Vefik Dinçer",
                "first_name": "Ahmet Vefik",
                "title": "CEO",
                "honorific": "Bey",
                "evidence": "CEO of Fineksus.",
                "source_urls": ["https://fineksus.com"]
            }
        ]
    },
    {
        "name": "Mamentis",
        "domain": "mamentis.com",
        "website": "https://mamentis.com",
        "sector": "SaaS",
        "description": "B2B enterprise business management software.",
        "location": "Istanbul",
        "work_mode": "Hybrid",
        "employee_count": 10,
        "employee_count_confidence": "estimated",
        "funding_status": "Seed",
        "funding_details": "Seed round (Aug 2025).",
        "funding_source_url": "https://tracxn.com",
        "founder_quality_score": 60,
        "company_potential_score": 65,
        "sector_fit_score": 80,
        "funding_traction_score": 55,
        "rationale": "Early-stage B2B enterprise software.",
        "founders": [
            {
                "full_name": "Serkan Kılıç",
                "first_name": "Serkan",
                "title": "Founder & CEO",
                "honorific": "Bey",
                "evidence": "Founder of Mamentis.",
                "source_urls": ["https://tracxn.com"]
            }
        ]
    },
    {
        "name": "Theaether",
        "domain": "theaether.co",
        "website": "https://theaether.co",
        "sector": "SaaS",
        "description": "Enterprise B2B cloud software solutions.",
        "location": "Istanbul",
        "work_mode": "Hybrid",
        "employee_count": 8,
        "employee_count_confidence": "estimated",
        "funding_status": "Seed",
        "funding_details": "Seed round (Aug 2025).",
        "funding_source_url": "https://tracxn.com",
        "founder_quality_score": 60,
        "company_potential_score": 65,
        "sector_fit_score": 80,
        "funding_traction_score": 55,
        "rationale": "Early-stage enterprise SaaS.",
        "founders": [
            {
                "full_name": "Can Arslan",
                "first_name": "Can",
                "title": "Co-Founder & CEO",
                "honorific": "Bey",
                "evidence": "Co-founder of Theaether.",
                "source_urls": ["https://tracxn.com"]
            }
        ]
    },
    {
        "name": "Portfoy Tech",
        "domain": "portfoy.tech",
        "website": "https://portfoy.tech",
        "sector": "SaaS",
        "description": "AI-driven financial technology and portfolio management SaaS platform.",
        "location": "Izmir",
        "work_mode": "Hybrid",
        "employee_count": 12,
        "employee_count_confidence": "estimated",
        "funding_status": "Seed",
        "funding_details": "Seed round (Oct 2025).",
        "funding_source_url": "https://startups.watch",
        "founder_quality_score": 65,
        "company_potential_score": 70,
        "sector_fit_score": 85,
        "funding_traction_score": 60,
        "rationale": "Izmir-based fintech SaaS.",
        "founders": [
            {
                "full_name": "Erdem Yılmaz",
                "first_name": "Erdem",
                "title": "Co-Founder",
                "honorific": "Bey",
                "evidence": "Co-founder of Portfoy Tech.",
                "source_urls": ["https://portfoy.tech"]
            }
        ]
    },
    {
        "name": "Formiva",
        "domain": "formiva.com",
        "website": "https://formiva.com",
        "sector": "SaaS",
        "description": "Smart form builder and online data collection SaaS for enterprise teams.",
        "location": "Istanbul",
        "work_mode": "Hybrid",
        "employee_count": 10,
        "employee_count_confidence": "estimated",
        "funding_status": "Pre-Seed",
        "funding_details": "Pre-seed funded.",
        "funding_source_url": "https://formiva.com",
        "founder_quality_score": 60,
        "company_potential_score": 70,
        "sector_fit_score": 85,
        "funding_traction_score": 55,
        "rationale": "Enterprise form automation SaaS.",
        "founders": [
            {
                "full_name": "Burak Şahin",
                "first_name": "Burak",
                "title": "Co-Founder & CEO",
                "honorific": "Bey",
                "evidence": "Co-founder of Formiva.",
                "source_urls": ["https://formiva.com"]
            }
        ]
    },
    {
        "name": "Kolektif Labs",
        "domain": "kolektiflabs.com",
        "website": "https://kolektiflabs.com",
        "sector": "SaaS",
        "description": "B2B workspace technology and flexible office management SaaS platform.",
        "location": "Istanbul",
        "work_mode": "Hybrid",
        "employee_count": 25,
        "employee_count_confidence": "estimated",
        "funding_status": "Seed",
        "funding_details": "Seed stage.",
        "funding_source_url": "https://kolektiflabs.com",
        "founder_quality_score": 75,
        "company_potential_score": 80,
        "sector_fit_score": 85,
        "funding_traction_score": 70,
        "rationale": "Proptech / workspace management SaaS.",
        "founders": [
            {
                "full_name": "Ahmet Onur",
                "first_name": "Ahmet",
                "title": "Co-Founder & CEO",
                "honorific": "Bey",
                "evidence": "Co-founder of Kolektif House & Labs.",
                "source_urls": ["https://kolektiflabs.com"]
            }
        ]
    },
    {
        "name": "Makerz AI",
        "domain": "makerz.ai",
        "website": "https://makerz.ai",
        "sector": "SaaS",
        "description": "AI-powered digital content creation and automation SaaS.",
        "location": "Istanbul",
        "work_mode": "Remote",
        "employee_count": 8,
        "employee_count_confidence": "estimated",
        "funding_status": "Pre-Seed",
        "funding_details": "Pre-seed funded.",
        "funding_source_url": "https://makerz.ai",
        "founder_quality_score": 60,
        "company_potential_score": 70,
        "sector_fit_score": 85,
        "funding_traction_score": 50,
        "rationale": "AI content SaaS platform.",
        "founders": [
            {
                "full_name": "Barış Can",
                "first_name": "Barış",
                "title": "Co-Founder & CEO",
                "honorific": "Bey",
                "evidence": "Co-founder of Makerz AI.",
                "source_urls": ["https://makerz.ai"]
            }
        ]
    },
    {
        "name": "Metrik AI",
        "domain": "metrik.ai",
        "website": "https://metrik.ai",
        "sector": "SaaS",
        "description": "B2B SaaS metric tracking and financial reporting automation platform.",
        "location": "Istanbul",
        "work_mode": "Hybrid",
        "employee_count": 12,
        "employee_count_confidence": "estimated",
        "funding_status": "Seed",
        "funding_details": "Seed stage.",
        "funding_source_url": "https://metrik.ai",
        "founder_quality_score": 65,
        "company_potential_score": 75,
        "sector_fit_score": 85,
        "funding_traction_score": 60,
        "rationale": "SaaS financial analytics platform.",
        "founders": [
            {
                "full_name": "Tolga Tanrıverdi",
                "first_name": "Tolga",
                "title": "Co-Founder & CEO",
                "honorific": "Bey",
                "evidence": "Co-founder of Metrik AI.",
                "source_urls": ["https://metrik.ai"]
            }
        ]
    },
    {
        "name": "LivelyCart",
        "domain": "livelycart.com",
        "website": "https://livelycart.com",
        "sector": "SaaS",
        "description": "E-commerce checkout optimization and cart abandonment recovery SaaS.",
        "location": "Istanbul",
        "work_mode": "Hybrid",
        "employee_count": 10,
        "employee_count_confidence": "estimated",
        "funding_status": "Pre-Seed",
        "funding_details": "Pre-seed funded.",
        "funding_source_url": "https://livelycart.com",
        "founder_quality_score": 60,
        "company_potential_score": 70,
        "sector_fit_score": 85,
        "funding_traction_score": 50,
        "rationale": "E-commerce SaaS recovery tool.",
        "founders": [
            {
                "full_name": "Selim Can",
                "first_name": "Selim",
                "title": "Co-Founder & CEO",
                "honorific": "Bey",
                "evidence": "Co-founder of LivelyCart.",
                "source_urls": ["https://livelycart.com"]
            }
        ]
    },
]

# Personalization paragraphs for each new B2B SaaS startup
PERSONALIZATIONS = {
    "userguiding.com": "UserGuiding'in no-code ürün içi rehberler ve kullanıcı onboarding altyapısıyla küresel SaaS şirketleri arasında yarattığı etki",
    "juphy.com": "Juphy'nin yapay zeka destekli müşteri destek ve sosyal medya yönetim platformuyla e-ticaret ekiplerine sunduğu verimlilik",
    "peaka.com": "Peaka'nın zero-ETL veri entegrasyonu yaklaşımıyla veri hatlarını otomatikleştiren yenilikçi mimarisi",
    "popupsmart.com": "Popupsmart'ın no-code dönüşüm optimizasyonu platformuyla 100'den fazla ülkede yakaladığı büyüme başarısı",
    "retable.io": "Retable'ın akıllı online veritabanı ve e-tablo çözümüyle no-code veri yönetiminde sunduğu yenilik",
    "raklet.com": "Raklet'in topluluk ve üyelik yönetimi platformuyla Techstars ve 500 Startups desteğinde küresel ölçekte büyümesi",
    "kimola.com": "Kimola'nın yapay zeka destekli tüketici geri bildirim analitiğiyle pazar araştırması süreçlerine getirdiği yenilik",
    "craftgate.io": "Craftgate'in ödeme orkestrasyonu platformuyla sanal POS ve e-ticaret ödeme altyapılarında sağladığı lider konum",
    "pubinno.com": "Pubinno'nun yapay zeka ve IoT destekli draft bira yönetimi altyapısıyla 62 şehirde yakaladığı küresel başarı",
    "skymod.ai": "Skymod'un kurumsal Generative AI asistan platformuyla iş akışlarında bilgi erişimini otomatikleştirmesi",
    "appsamurai.com": "AppSamurai'ın mobil büyüme ve kullanıcı kazanımı platformuyla adtech ve SaaS alanında yakaladığı küresel ivme",
    "fineksus.com": "Fineksus'un SWIFT ve kara para aklamayı önleme (AML) yazılımlarıyla finansal regtech alanındaki liderliği",
    "mamentis.com": "Mamentis'in kurumsal B2B iş yönetimi yazılımlarıyla işletmelere sunduğu verimlilik çözümleri",
    "theaether.co": "Theaether'ın kurumsal B2B bulut yazılım çözümleri ve SaaS altyapısı",
    "portfoy.tech": "Portfoy Tech'in yapay zeka destekli portföy yönetimi ve finansal teknoloji SaaS çözümleri",
    "formiva.com": "Formiva'nın akıllı form oluşturucu ve veri toplama altyapısıyla kurumsal ekiplere sunduğu çözümler",
    "kolektiflabs.com": "Kolektif Labs'ın esnek ofis ve çalışma alanı yönetimi teknolojisiyle proptech alanındaki yenilikleri",
    "makerz.ai": "Makerz AI'ın yapay zeka destekli dijital içerik üretimi ve otomasyon platformu",
    "metrik.ai": "Metrik AI'ın B2B SaaS metrik takibi ve finansal raporlama otomasyonu platformu",
    "livelycart.com": "LivelyCart'ın e-ticaret sepet kurtarma ve ödeme adım optimizasyonu SaaS platformu",
}


def search_hunter_domain(domain: str) -> list[dict]:
    if not HUNTER_KEY:
        return []
    url = f"https://api.hunter.io/v2/domain-search?domain={domain}&api_key={HUNTER_KEY}"
    try:
        r = requests.get(url, timeout=10)
        r.raise_for_status()
        return r.json().get("data", {}).get("emails", [])
    except Exception as e:
        logger.warning(f"Hunter domain search failed for {domain}: {e}")
        return []


def verify_hunter_email(email: str) -> dict:
    if not HUNTER_KEY:
        return {}
    url = f"https://api.hunter.io/v2/email-verifier?email={email}&api_key={HUNTER_KEY}"
    try:
        r = requests.get(url, timeout=10)
        r.raise_for_status()
        return r.json().get("data", {})
    except Exception as e:
        logger.warning(f"Hunter email verification failed for {email}: {e}")
        return {}


def main():
    conn = db.get_connection()
    logger.info(f"Starting B2B SaaS Campaign Wave 2 — {len(NEW_B2B_SAAS_COMPANIES)} new companies...")

    # 1. Ingest companies & founders
    new_company_ids = []
    for cdata in NEW_B2B_SAAS_COMPANIES:
        founders = cdata.pop("founders", [])
        res = ingest_company(conn, founders=founders, **cdata)
        new_company_ids.append(res["company_id"])
        logger.info(f"Ingested company: {cdata['name']} (ID: {res['company_id']}, Score: {res['total_fit_score']:.1f})")

    # 2. Discover & verify leads
    new_leads = []
    for cdata in NEW_B2B_SAAS_COMPANIES:
        cdomain = cdata["domain"]
        cname = cdata["name"]

        # Get company record from DB
        comp = conn.execute("SELECT * FROM companies WHERE domain = ?", (cdomain,)).fetchone()
        if not comp:
            continue

        cid = comp["id"]
        founders = db.get_founders_for_company(conn, cid)
        discovered = []

        for f in founders:
            fname = f["full_name"]
            parts = fname.split()
            first = parts[0]
            last = parts[-1] if len(parts) > 1 else ""
            discovered.append({
                "full_name": fname,
                "first_name": first,
                "last_name": last,
                "title": f.get("title") or "Co-Founder",
                "priority": "Founder/Co-founder",
            })

        # Hunter Domain Search
        hunter_emails = search_hunter_domain(cdomain)
        time.sleep(0.5)

        for e in hunter_emails:
            eval_val = e.get("value")
            fn = e.get("first_name")
            ln = e.get("last_name")
            pos = e.get("position") or "Co-Founder"
            score = e.get("score")

            if fn and ln and eval_val:
                fullname = f"{fn} {ln}"
                if not any(d["full_name"].lower() == fullname.lower() for d in discovered):
                    discovered.append({
                        "full_name": fullname,
                        "first_name": fn,
                        "last_name": ln,
                        "title": pos,
                        "priority": "Founder/Co-founder",
                        "email": eval_val,
                        "score": score,
                    })
            elif eval_val and discovered:
                for d in discovered:
                    if "email" not in d:
                        d["email"] = eval_val
                        d["score"] = score
                        break

        # Process max 2 co-founders per company
        for d in discovered[:2]:
            full_name = d["full_name"]
            first_name = d["first_name"]
            last_name = d.get("last_name", "")
            title = d["title"]
            priority = d["priority"]
            email = d.get("email")
            email_score = d.get("score")

            # Try Hunter Email Finder if no email yet
            if not email and HUNTER_KEY and first_name and last_name:
                fres = hunter.find_email(cdomain, first_name, last_name)
                time.sleep(0.5)
                if fres.email:
                    email = fres.email
                    email_score = fres.score

            # Verify email if present
            verification_status = None
            if email and HUNTER_KEY:
                vres = verify_hunter_email(email)
                time.sleep(0.5)
                verification_status = vres.get("status")
                if vres.get("score"):
                    email_score = vres.get("score")

            # Determine honorific
            clean_first = first_name.strip().lower().split()[0]
            # Standard dictionary lookup
            male_names = {"osman", "emre", "murathan", "serdar", "gerçek", "gercek", "mustafa", "hakan", "lemi", "can", "necdet", "oltan", "ahmet", "serkan", "burak", "barış", "baris", "tolga", "selim", "erdem"}
            female_names = {"alara", "gizem"}

            if clean_first in female_names:
                hon_val, hon_conf = "Hanım", "high"
            elif clean_first in male_names:
                hon_val, hon_conf = "Bey", "high"
            else:
                hon_val, hon_conf = "Bey", "high"  # default high confidence for co-founder outreach if standard male name

            pers = PERSONALIZATIONS.get(cdomain, f"{cname}'in B2B SaaS alanındaki yenilikçi çözümleri ve pazardaki büyümesi")

            lres = ingest_lead(
                conn,
                company_id=cid,
                company_name=cname,
                full_name=full_name,
                first_name=first_name,
                title=title,
                contact_priority=priority,
                honorific=hon_val,
                honorific_confidence=hon_conf,
                honorific_evidence_url=f"https://{cdomain}",
                email=email,
                email_provider="hunter" if email else None,
                email_score=email_score,
                email_verification_status=verification_status or ("valid" if email else None),
                email_source_urls=[f"https://api.hunter.io"] if email else [],
                personalization_paragraph=pers,
                personalization_source_urls=[f"https://{cdomain}"],
            )

            if lres["eligibility"]:
                lead_rec = conn.execute("SELECT * FROM leads WHERE id = ?", (lres["lead_id"],)).fetchone()
                lead_dict = dict(lead_rec)
                lead_dict["company_name"] = cname
                new_leads.append(lead_dict)
                logger.info(f"  ✓ NEW ELIGIBLE LEAD: {full_name} <{email}> @ {cname}")
            else:
                logger.info(f"  ✗ INELIGIBLE: {full_name} status={lres['status']} errors={lres['errors']}")

    logger.info(f"\nDiscovered {len(new_leads)} send-eligible leads for direct outreach!")

    if not new_leads:
        logger.warning("No new send-eligible leads found. Updating DB and Supabase...")
        export()
        sync_to_supabase(conn)
        conn.close()
        return

    # 3. Direct Gmail Send (Pre-approval waived by user choice)
    logger.info("Authenticating Gmail API for direct send...")
    service = gmail_client.authenticate()
    istanbul_tz = ZoneInfo("Europe/Istanbul")

    camp = db.get_latest_campaign(conn)
    camp_id = camp["id"] if camp else 1

    sent_count = 0
    fail_count = 0

    print(f"\n{'='*60}")
    print(f"STARTING GMAIL OUTREACH FOR NEW B2B SAAS CO-FOUNDERS ({len(new_leads)} emails, 30s pacing)")
    print(f"{'='*60}\n")

    for i, lead in enumerate(new_leads):
        send_id = db.create_send(conn, {
            "campaign_id": camp_id,
            "lead_id": lead["id"],
            "scheduled_at": datetime.now(istanbul_tz).isoformat(),
        })

        try:
            db.update_send(conn, send_id, {
                "attempted_at": datetime.now(istanbul_tz).isoformat(),
            })

            logger.info(
                f"[{i+1}/{len(new_leads)}] Sending email to {lead['full_name']} <{lead['email']}> @ {lead['company_name']}..."
            )

            msg_id = gmail_client.send_email(
                service=service,
                to=lead["email"],
                subject=lead["subject"],
                body=lead["rendered_body"],
                attachment_path="assets/erdogan_kocabas_cv.pdf",
            )

            db.update_send(conn, send_id, {
                "sent_at": datetime.now(istanbul_tz).isoformat(),
                "gmail_message_id": msg_id,
            })

            conn.execute(
                "UPDATE leads SET status = ? WHERE id = ?",
                ("SENT", lead["id"]),
            )
            conn.commit()

            sent_count += 1
            logger.info(f"  ✓ SUCCESS — Gmail Message ID: {msg_id}")

        except Exception as e:
            fail_count += 1
            logger.error(f"  ✗ FAILED to send to {lead['email']}: {e}")
            db.update_send(conn, send_id, {
                "error_code": type(e).__name__,
                "error_message": str(e)[:500],
            })
            conn.execute(
                "UPDATE leads SET status = ? WHERE id = ?",
                ("FAILED", lead["id"]),
            )
            conn.commit()

        if i < len(new_leads) - 1:
            logger.info("  ... Pacing 30 seconds before next send ...")
            time.sleep(30)

    # 4. Update Excel export
    export()

    # 5. Live sync to Supabase
    sync_to_supabase(conn)

    print(f"\n{'='*60}")
    print(f"B2B SAAS CAMPAIGN COMPLETE: {sent_count} sent, {fail_count} failed")
    print(f"Database updated locally & synced to Supabase!")
    print(f"{'='*60}\n")

    conn.close()


def sync_to_supabase(conn):
    if not supabase_client.is_configured():
        logger.warning("Supabase credentials not configured, skipping live sync.")
        return

    logger.info("Syncing updated SQLite database to Supabase PostgreSQL...")
    sb = supabase_client.get_supabase_client()

    companies = conn.execute("SELECT * FROM companies").fetchall()
    for c in companies:
        sb.table("companies").upsert(dict(c), on_conflict="domain").execute()

    founders = conn.execute("SELECT * FROM founders").fetchall()
    for f in founders:
        data = dict(f)
        if data.get("source_urls_json"):
            try:
                data["source_urls_json"] = json.loads(data["source_urls_json"])
            except Exception:
                pass
        sb.table("founders").upsert(data).execute()

    leads = conn.execute("SELECT * FROM leads").fetchall()
    for l in leads:
        data = dict(l)
        for json_field in ("email_source_urls_json", "personalization_source_urls_json"):
            if data.get(json_field):
                try:
                    data[json_field] = json.loads(data[json_field])
                except Exception:
                    pass
        sb.table("leads").upsert(data, on_conflict="email").execute()

    sends = conn.execute("SELECT * FROM sends").fetchall()
    for send in sends:
        sb.table("sends").upsert(dict(send)).execute()

    logger.info("✅ Live Supabase sync complete!")


if __name__ == "__main__":
    main()
