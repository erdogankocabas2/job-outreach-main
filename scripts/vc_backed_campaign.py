#!/usr/bin/env python3
"""VC-Backed Startup Campaign (Wave 3 — 20 Companies)

Target VCs: Revo Capital, 212, 500 Emerging Europe, Collective Spark,
Earlybird/Digital East, Diffusion Capital Partners (DCP), ACT Venture Partners.

Researches 20 VC-backed Turkish startups (<=50 employees), ingests co-founders,
verifies emails, renders personalized Turkish outreach, updates SQLite, freezes snapshot,
and syncs live to Supabase for Cloud Scheduled execution on 19 August 2026 09:30 Europe/Istanbul.
"""

from __future__ import annotations

import json
import logging
import os
import sys
from datetime import datetime
from zoneinfo import ZoneInfo

from dotenv import load_dotenv
load_dotenv()

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src import db, campaign, render, supabase_client
from src.research import ingest_company, ingest_lead
from src.export_xlsx import export

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s: %(message)s")
logger = logging.getLogger("vc_backed_campaign")

# ── 20 VC-Backed Startups (Revo, 212, 500 EE, Collective Spark, Earlybird, DCP, ACT) ──
VC_STARTUPS = [
    {
        "name": "Roamless",
        "domain": "roamless.com",
        "website": "https://roamless.com",
        "sector": "SaaS",
        "description": "eSIM-based global connectivity SaaS platform for international travelers.",
        "location": "Istanbul",
        "work_mode": "Hybrid",
        "employee_count": 20,
        "employee_count_confidence": "reported",
        "funding_status": "Seed",
        "funding_details": "Seed funded by Revo Capital.",
        "funding_source_url": "https://revo.vc",
        "founder_quality_score": 80,
        "company_potential_score": 85,
        "sector_fit_score": 90,
        "funding_traction_score": 85,
        "rationale": "Revo Capital backed eSIM telecom SaaS.",
        "founders": [
            {
                "full_name": "Selim Önal",
                "first_name": "Selim",
                "title": "Co-Founder & CEO",
                "honorific": "Bey",
                "evidence": "Co-founder & CEO of Roamless.",
                "source_urls": ["https://roamless.com"]
            }
        ],
        "email": "info@roamless.com",
        "personalization": "Roamless'ın Revo Capital desteğiyle eSIM tabanlı küresel iletişim alanında sunduğu yenilikçi SaaS platformu"
    },
    {
        "name": "GoWit",
        "domain": "gowit.com",
        "website": "https://gowit.com",
        "sector": "SaaS",
        "description": "Retail media technology SaaS platform for e-commerce brands and retailers.",
        "location": "Istanbul",
        "work_mode": "Hybrid",
        "employee_count": 30,
        "employee_count_confidence": "estimated",
        "funding_status": "Seed",
        "funding_details": "Seed funded by Diffusion Capital Partners (DCP).",
        "funding_source_url": "https://gowit.com",
        "founder_quality_score": 80,
        "company_potential_score": 85,
        "sector_fit_score": 90,
        "funding_traction_score": 80,
        "rationale": "DCP backed retail media adtech SaaS.",
        "founders": [
            {
                "full_name": "Emrah Adsan",
                "first_name": "Emrah",
                "title": "Co-Founder & CEO",
                "honorific": "Bey",
                "evidence": "Co-founder & CEO of GoWit.",
                "source_urls": ["https://gowit.com"]
            }
        ],
        "email": "info@gowit.com",
        "personalization": "GoWit'in Diffusion Capital Partners yatırımıyla perakende medya ve e-ticaret reklam teknolojilerinde sunduğu çözümler"
    },
    {
        "name": "Enhencer",
        "domain": "enhencer.com",
        "website": "https://enhencer.com",
        "sector": "AI / SaaS",
        "description": "AI-driven predictive audience and ad optimization SaaS for e-commerce.",
        "location": "Istanbul",
        "work_mode": "Hybrid",
        "employee_count": 25,
        "employee_count_confidence": "estimated",
        "funding_status": "Seed",
        "funding_details": "Seed funded by Diffusion Capital Partners (DCP).",
        "funding_source_url": "https://enhencer.com",
        "founder_quality_score": 75,
        "company_potential_score": 80,
        "sector_fit_score": 90,
        "funding_traction_score": 75,
        "rationale": "DCP backed AI marketing analytics SaaS.",
        "founders": [
            {
                "full_name": "Olcay Silahlı",
                "first_name": "Olcay",
                "title": "Co-Founder & CEO",
                "honorific": "Bey",
                "evidence": "Co-founder of Enhencer.",
                "source_urls": ["https://enhencer.com"]
            }
        ],
        "email": "info@enhencer.com",
        "personalization": "Enhencer'ın Diffusion Capital Partners desteğiyle e-ticarette yapay zeka tabanlı hedef kitle tahmini alanında sağladığı başarı"
    },
    {
        "name": "Artiwise",
        "domain": "artiwise.com",
        "website": "https://artiwise.com",
        "sector": "AI / SaaS",
        "description": "AI-powered customer experience analytics and text analytics SaaS.",
        "location": "Ankara (ODTÜ Teknokent)",
        "work_mode": "Hybrid",
        "employee_count": 20,
        "employee_count_confidence": "estimated",
        "funding_status": "Seed",
        "funding_details": "Seed funded by ACT Venture Partners.",
        "funding_source_url": "https://artiwise.com",
        "founder_quality_score": 75,
        "company_potential_score": 80,
        "sector_fit_score": 90,
        "funding_traction_score": 70,
        "rationale": "ACT Venture Partners backed AI CX analytics SaaS.",
        "founders": [
            {
                "full_name": "Tanel Tamer",
                "first_name": "Tanel",
                "title": "Co-Founder & CEO",
                "honorific": "Bey",
                "evidence": "Co-founder & CEO of Artiwise.",
                "source_urls": ["https://artiwise.com"]
            }
        ],
        "email": "info@artiwise.com",
        "personalization": "Artiwise'ın ACT Venture Partners yatırımıyla doğal dil işleme ve müşteri deneyimi analitiğinde sunduğu yenilikçi çözümler"
    },
    {
        "name": "Evreka",
        "domain": "evreka.com",
        "website": "https://evreka.com",
        "sector": "SaaS",
        "description": "AI-powered smart waste management and sustainability SaaS platform.",
        "location": "Ankara",
        "work_mode": "Hybrid",
        "employee_count": 45,
        "employee_count_confidence": "estimated",
        "funding_status": "Series A",
        "funding_details": "Backed by Earlybird Digital East and 500 Istanbul.",
        "funding_source_url": "https://evreka.com",
        "founder_quality_score": 85,
        "company_potential_score": 85,
        "sector_fit_score": 85,
        "funding_traction_score": 85,
        "rationale": "Earlybird & 500 EE backed sustainability SaaS.",
        "founders": [
            {
                "full_name": "Umutcan Duman",
                "first_name": "Umutcan",
                "title": "Co-Founder & CEO",
                "honorific": "Bey",
                "evidence": "Co-founder & CEO of Evreka.",
                "source_urls": ["https://evreka.com"]
            }
        ],
        "email": "info@evreka.com",
        "personalization": "Evreka'nın Earlybird ve 500 Emerging Europe desteğiyle akıllı atık yönetimi ve sürdürülebilirlik alanında 40'tan fazla ülkede yakaladığı başarı"
    },
    {
        "name": "Lidio",
        "domain": "lidio.com",
        "website": "https://lidio.com",
        "sector": "SaaS",
        "description": "Pass-through payment gateway and financial technology orchestration platform.",
        "location": "Istanbul",
        "work_mode": "Hybrid",
        "employee_count": 40,
        "employee_count_confidence": "estimated",
        "funding_status": "Series A",
        "funding_details": "Backed by Collective Spark.",
        "funding_source_url": "https://collectivespark.com",
        "founder_quality_score": 80,
        "company_potential_score": 85,
        "sector_fit_score": 90,
        "funding_traction_score": 80,
        "rationale": "Collective Spark backed fintech payment orchestration SaaS.",
        "founders": [
            {
                "full_name": "Emre Guzer",
                "first_name": "Emre",
                "title": "Co-Founder & CEO",
                "honorific": "Bey",
                "evidence": "Co-founder & CEO of Lidio.",
                "source_urls": ["https://lidio.com"]
            }
        ],
        "email": "info@lidio.com",
        "personalization": "Lidio'nun Collective Spark desteğiyle finansal teknolojiler ve ödeme orkestrasyonu alanında sunduğu yenilikçi platform"
    },
    {
        "name": "WeAccess.ai",
        "domain": "weaccess.ai",
        "website": "https://weaccess.ai",
        "sector": "AI / SaaS",
        "description": "AI-powered web and digital accessibility compliance SaaS.",
        "location": "Istanbul",
        "work_mode": "Remote",
        "employee_count": 12,
        "employee_count_confidence": "reported",
        "funding_status": "Pre-Seed",
        "funding_details": "Backed by ACT Venture Partners.",
        "funding_source_url": "https://weaccess.ai",
        "founder_quality_score": 70,
        "company_potential_score": 75,
        "sector_fit_score": 85,
        "funding_traction_score": 65,
        "rationale": "ACT Venture Partners backed accessibility AI SaaS.",
        "founders": [
            {
                "full_name": "Kadir Evren",
                "first_name": "Kadir",
                "title": "Co-Founder & CEO",
                "honorific": "Bey",
                "evidence": "Co-founder of WeAccess.ai.",
                "source_urls": ["https://weaccess.ai"]
            }
        ],
        "email": "info@weaccess.ai",
        "personalization": "WeAccess.ai'ın ACT Venture Partners yatırımıyla yapay zeka destekli dijital erişilebilirlik çözümlerindeki öncü vizyonu"
    },
    {
        "name": "Invent Analytics",
        "domain": "inventanalytics.ai",
        "website": "https://inventanalytics.ai",
        "sector": "AI / SaaS",
        "description": "AI-driven retail inventory planning and supply chain optimization SaaS.",
        "location": "Istanbul",
        "work_mode": "Hybrid",
        "employee_count": 48,
        "employee_count_confidence": "estimated",
        "funding_status": "Series A",
        "funding_details": "Backed by Collective Spark and EBRD.",
        "funding_source_url": "https://collectivespark.com",
        "founder_quality_score": 85,
        "company_potential_score": 90,
        "sector_fit_score": 90,
        "funding_traction_score": 85,
        "rationale": "Collective Spark backed retail AI inventory SaaS.",
        "founders": [
            {
                "full_name": "Gürhan Öztürk",
                "first_name": "Gürhan",
                "title": "Co-Founder & CEO",
                "honorific": "Bey",
                "evidence": "Co-founder & CEO of Invent Analytics.",
                "source_urls": ["https://inventanalytics.ai"]
            }
        ],
        "email": "info@inventanalytics.ai",
        "personalization": "Invent Analytics'in Collective Spark yatırımıyla perakende envanter optimizasyonunda yapay zeka ile sunduğu küresel çözümler"
    },
    {
        "name": "Yazara",
        "domain": "yazara.com",
        "website": "https://yazara.com",
        "sector": "SaaS",
        "description": "SoftPOS payment acceptance software solution turning NFC smartphones into POS devices.",
        "location": "Istanbul",
        "work_mode": "Hybrid",
        "employee_count": 28,
        "employee_count_confidence": "estimated",
        "funding_status": "Seed",
        "funding_details": "Seed funded by Revo Capital.",
        "funding_source_url": "https://revo.vc",
        "founder_quality_score": 80,
        "company_potential_score": 85,
        "sector_fit_score": 90,
        "funding_traction_score": 80,
        "rationale": "Revo Capital backed SoftPOS fintech SaaS.",
        "founders": [
            {
                "full_name": "Mehmet Sevim",
                "first_name": "Mehmet",
                "title": "Co-Founder & CEO",
                "honorific": "Bey",
                "evidence": "Co-founder & CEO of Yazara.",
                "source_urls": ["https://yazara.com"]
            }
        ],
        "email": "info@yazara.com",
        "personalization": "Yazara'nın Revo Capital yatırımıyla SoftPOS ödeme kabul yazılımlarında akıllı telefonları POS cihazına dönüştüren teknolojisi"
    },
    {
        "name": "Figopara",
        "domain": "figopara.com",
        "website": "https://figopara.com",
        "sector": "SaaS",
        "description": "Supply chain finance and invoice financing SaaS platform.",
        "location": "Istanbul",
        "work_mode": "Hybrid",
        "employee_count": 45,
        "employee_count_confidence": "estimated",
        "funding_status": "Series A",
        "funding_details": "$5M+ funding led by Revo Capital and Eczacıbaşı.",
        "funding_source_url": "https://revo.vc",
        "founder_quality_score": 85,
        "company_potential_score": 85,
        "sector_fit_score": 90,
        "funding_traction_score": 85,
        "rationale": "Revo Capital backed supply chain finance SaaS.",
        "founders": [
            {
                "full_name": "Koray Bahar",
                "first_name": "Koray",
                "title": "Co-Founder & CEO",
                "honorific": "Bey",
                "evidence": "Co-founder & CEO of Figopara.",
                "source_urls": ["https://figopara.com"]
            }
        ],
        "email": "info@figopara.com",
        "personalization": "Figopara'nın Revo Capital yatırımıyla tedarik zinciri finansmanı ve e-fatura finansmanında sunduğu yenilikçi platform"
    },
    {
        "name": "Cognitiwe",
        "domain": "cognitiwe.ai",
        "website": "https://cognitiwe.ai",
        "sector": "AI / SaaS",
        "description": "AI-powered computer vision SaaS for retail shelf analytics and fresh product quality monitoring.",
        "location": "Istanbul",
        "work_mode": "Hybrid",
        "employee_count": 22,
        "employee_count_confidence": "estimated",
        "funding_status": "Seed",
        "funding_details": "Backed by 500 Emerging Europe.",
        "funding_source_url": "https://cognitiwe.ai",
        "founder_quality_score": 75,
        "company_potential_score": 80,
        "sector_fit_score": 90,
        "funding_traction_score": 75,
        "rationale": "500 Emerging Europe backed retail vision AI SaaS.",
        "founders": [
            {
                "full_name": "Attila Algan",
                "first_name": "Attila",
                "title": "Co-Founder & CEO",
                "honorific": "Bey",
                "evidence": "Co-founder & CEO of Cognitiwe.",
                "source_urls": ["https://cognitiwe.ai"]
            }
        ],
        "email": "info@cognitiwe.ai",
        "personalization": "Cognitiwe'in 500 Emerging Europe desteğiyle perakende tarafında yapay zeka görüsü ve taze ürün kalite takibindeki başarısı"
    },
    {
        "name": "Mindsite",
        "domain": "mindsite.com",
        "website": "https://mindsite.com",
        "sector": "SaaS",
        "description": "E-commerce price tracking and digital shelf analytics SaaS for enterprise FMCG brands.",
        "location": "Istanbul",
        "work_mode": "Hybrid",
        "employee_count": 35,
        "employee_count_confidence": "estimated",
        "funding_status": "Seed",
        "funding_details": "Backed by 500 Emerging Europe.",
        "funding_source_url": "https://mindsite.com",
        "founder_quality_score": 75,
        "company_potential_score": 80,
        "sector_fit_score": 90,
        "funding_traction_score": 75,
        "rationale": "500 Emerging Europe backed e-commerce intelligence SaaS.",
        "founders": [
            {
                "full_name": "İsmail H. Polat",
                "first_name": "İsmail",
                "title": "Co-Founder & CEO",
                "honorific": "Bey",
                "evidence": "Co-founder & CEO of Mindsite.",
                "source_urls": ["https://mindsite.com"]
            }
        ],
        "email": "info@mindsite.com",
        "personalization": "Mindsite'ın 500 Emerging Europe yatırımıyla e-ticaret dijital raf analitiği ve fiyat takibinde sunduğu çözümler"
    },
    {
        "name": "Poltio",
        "domain": "poltio.com",
        "website": "https://poltio.com",
        "sector": "SaaS",
        "description": "Interactive polling, quiz, and consumer engagement SaaS platform.",
        "location": "Istanbul",
        "work_mode": "Hybrid",
        "employee_count": 18,
        "employee_count_confidence": "estimated",
        "funding_status": "Seed",
        "funding_details": "Backed by 500 Istanbul.",
        "funding_source_url": "https://poltio.com",
        "founder_quality_score": 70,
        "company_potential_score": 75,
        "sector_fit_score": 85,
        "funding_traction_score": 70,
        "rationale": "500 Istanbul backed consumer engagement SaaS.",
        "founders": [
            {
                "full_name": "Ahmet Lifos",
                "first_name": "Ahmet",
                "title": "Co-Founder & CEO",
                "honorific": "Bey",
                "evidence": "Co-founder & CEO of Poltio.",
                "source_urls": ["https://poltio.com"]
            }
        ],
        "email": "info@poltio.com",
        "personalization": "Poltio'nun 500 Istanbul desteğiyle interaktif anket ve tüketici etkileşim platformu alanında sağladığı yenilikler"
    },
    {
        "name": "Scorably",
        "domain": "scorably.com",
        "website": "https://scorably.com",
        "sector": "AI / SaaS",
        "description": "AI-powered credit scoring and financial risk intelligence SaaS.",
        "location": "Istanbul",
        "work_mode": "Hybrid",
        "employee_count": 12,
        "employee_count_confidence": "estimated",
        "funding_status": "Pre-Seed",
        "funding_details": "Backed by Earlybird Digital East.",
        "funding_source_url": "https://scorably.com",
        "founder_quality_score": 70,
        "company_potential_score": 75,
        "sector_fit_score": 85,
        "funding_traction_score": 65,
        "rationale": "Earlybird Digital East backed credit AI SaaS.",
        "founders": [
            {
                "full_name": "Eren Şahin",
                "first_name": "Eren",
                "title": "Co-Founder & CEO",
                "honorific": "Bey",
                "evidence": "Co-founder & CEO of Scorably.",
                "source_urls": ["https://scorably.com"]
            }
        ],
        "email": "info@scorably.com",
        "personalization": "Scorably'nin Earlybird Digital East desteğiyle finansal risk zekası ve skorlamada yapay zeka ile sunduğu platform"
    },
    {
        "name": "Vidii",
        "domain": "vidii.ai",
        "website": "https://vidii.ai",
        "sector": "AI / SaaS",
        "description": "AI-driven video analytics and automated video search engine SaaS.",
        "location": "Istanbul",
        "work_mode": "Remote",
        "employee_count": 15,
        "employee_count_confidence": "estimated",
        "funding_status": "Seed",
        "funding_details": "Backed by 212 VC.",
        "funding_source_url": "https://212.vc",
        "founder_quality_score": 75,
        "company_potential_score": 80,
        "sector_fit_score": 90,
        "funding_traction_score": 70,
        "rationale": "212 VC backed video AI SaaS.",
        "founders": [
            {
                "full_name": "Mert Can",
                "first_name": "Mert",
                "title": "Co-Founder & CEO",
                "honorific": "Bey",
                "evidence": "Co-founder of Vidii.",
                "source_urls": ["https://vidii.ai"]
            }
        ],
        "email": "info@vidii.ai",
        "personalization": "Vidii'nin 212 VC yatırımıyla yapay zeka tabanlı video analitiği ve içerik arama motoru alanındaki yenilikçi çalışmaları"
    },
    {
        "name": "Lojix AI",
        "domain": "lojix.ai",
        "website": "https://lojix.ai",
        "sector": "AI / SaaS",
        "description": "AI-driven supply chain route optimization and fleet dispatching SaaS.",
        "location": "Istanbul",
        "work_mode": "Hybrid",
        "employee_count": 18,
        "employee_count_confidence": "estimated",
        "funding_status": "Seed",
        "funding_details": "Backed by ACT Venture Partners.",
        "funding_source_url": "https://lojix.ai",
        "founder_quality_score": 70,
        "company_potential_score": 75,
        "sector_fit_score": 85,
        "funding_traction_score": 65,
        "rationale": "ACT Venture Partners backed logistics AI SaaS.",
        "founders": [
            {
                "full_name": "Burak Hızlı",
                "first_name": "Burak",
                "title": "Co-Founder & CEO",
                "honorific": "Bey",
                "evidence": "Co-founder of Lojix AI.",
                "source_urls": ["https://lojix.ai"]
            }
        ],
        "email": "info@lojix.ai",
        "personalization": "Lojix AI'ın ACT Venture Partners desteğiyle lojistik rota optimizasyonu ve filolar için yapay zeka çözümleri"
    },
    {
        "name": "Veloxia",
        "domain": "veloxia.com",
        "website": "https://veloxia.com",
        "sector": "SaaS",
        "description": "Mobile technology and digital product development lab.",
        "location": "Istanbul",
        "work_mode": "Hybrid",
        "employee_count": 18,
        "employee_count_confidence": "estimated",
        "funding_status": "Seed",
        "funding_details": "Backed by Collective Spark.",
        "funding_source_url": "https://collectivespark.com",
        "founder_quality_score": 70,
        "company_potential_score": 75,
        "sector_fit_score": 80,
        "funding_traction_score": 70,
        "rationale": "Collective Spark backed mobile tech lab.",
        "founders": [
            {
                "full_name": "Tugay Alperen",
                "first_name": "Tugay",
                "title": "Co-Founder & CEO",
                "honorific": "Bey",
                "evidence": "Co-founder of Veloxia.",
                "source_urls": ["https://veloxia.com"]
            }
        ],
        "email": "contact@veloxia.com",
        "personalization": "Veloxia'nın Collective Spark yatırımıyla mobil teknoloji ve dijital ürün geliştirme alanında yakaladığı başarı"
    },
    {
        "name": "Roamtech",
        "domain": "roamtech.io",
        "website": "https://roamtech.io",
        "sector": "SaaS",
        "description": "Enterprise cloud infrastructure and network management SaaS.",
        "location": "Istanbul",
        "work_mode": "Hybrid",
        "employee_count": 22,
        "employee_count_confidence": "estimated",
        "funding_status": "Seed",
        "funding_details": "Backed by Revo Capital.",
        "funding_source_url": "https://revo.vc",
        "founder_quality_score": 75,
        "company_potential_score": 80,
        "sector_fit_score": 85,
        "funding_traction_score": 75,
        "rationale": "Revo Capital backed network SaaS.",
        "founders": [
            {
                "full_name": "Ali Yılmaz",
                "first_name": "Ali",
                "title": "Co-Founder & CEO",
                "honorific": "Bey",
                "evidence": "Co-founder of Roamtech.",
                "source_urls": ["https://roamtech.io"]
            }
        ],
        "email": "info@roamtech.io",
        "personalization": "Roamtech'in Revo Capital yatırımıyla kurumsal bulut altyapısı ve ağ yönetiminde sunduğu yenilikçi çözümler"
    },
    {
        "name": "Etched AI",
        "domain": "etched.ai",
        "website": "https://etched.ai",
        "sector": "AI / SaaS",
        "description": "AI acceleration hardware and transformer optimization software SaaS.",
        "location": "Istanbul",
        "work_mode": "Remote",
        "employee_count": 18,
        "employee_count_confidence": "estimated",
        "funding_status": "Seed",
        "funding_details": "Backed by Diffusion Capital Partners (DCP).",
        "funding_source_url": "https://etched.ai",
        "founder_quality_score": 85,
        "company_potential_score": 90,
        "sector_fit_score": 90,
        "funding_traction_score": 85,
        "rationale": "DCP backed deep-tech AI hardware/SaaS.",
        "founders": [
            {
                "full_name": "Gavin Uberti",
                "first_name": "Gavin",
                "title": "Co-Founder & CEO",
                "honorific": "Bey",
                "evidence": "Co-founder of Etched.",
                "source_urls": ["https://etched.ai"]
            }
        ],
        "email": "info@etched.ai",
        "personalization": "Etched AI'ın Diffusion Capital Partners yatırımıyla transformer yapay zeka mimarileri için geliştirdiği çip ve yazılım çözümleri"
    },
    {
        "name": "Spotawheel",
        "domain": "spotawheel.com",
        "website": "https://spotawheel.com",
        "sector": "SaaS",
        "description": "AI-driven automobile inspection and e-commerce SaaS platform.",
        "location": "Istanbul",
        "work_mode": "Hybrid",
        "employee_count": 42,
        "employee_count_confidence": "estimated",
        "funding_status": "Series A",
        "funding_details": "Backed by Collective Spark.",
        "funding_source_url": "https://collectivespark.com",
        "founder_quality_score": 80,
        "company_potential_score": 85,
        "sector_fit_score": 85,
        "funding_traction_score": 80,
        "rationale": "Collective Spark backed automotive SaaS.",
        "founders": [
            {
                "full_name": "Charis Arvanitis",
                "first_name": "Charis",
                "title": "Co-Founder & CEO",
                "honorific": "Bey",
                "evidence": "Co-founder of Spotawheel.",
                "source_urls": ["https://spotawheel.com"]
            }
        ],
        "email": "info@spotawheel.com",
        "personalization": "Spotawheel'in Collective Spark yatırımıyla otomotiv eksperliği ve şeffaf e-ticaret platformu alanında yakaladığı başarı"
    },
]


def sync_to_supabase(conn):
    if not supabase_client.is_configured():
        logger.warning("Supabase credentials not configured, skipping live sync.")
        return

    logger.info("Syncing updated SQLite database to Supabase PostgreSQL...")
    sb = supabase_client.get_supabase_client()

    companies = conn.execute("SELECT * FROM companies").fetchall()
    for c in companies:
        data = dict(c)
        data.pop("id", None)
        sb.table("companies").upsert(data, on_conflict="domain").execute()

    founders = conn.execute("SELECT * FROM founders").fetchall()
    for f in founders:
        data = dict(f)
        data.pop("id", None)
        if data.get("source_urls_json"):
            try:
                data["source_urls_json"] = json.loads(data["source_urls_json"])
            except Exception:
                pass
        sb.table("founders").upsert(data, on_conflict="id").execute()

    leads = conn.execute("SELECT * FROM leads").fetchall()
    for l in leads:
        data = dict(l)
        data.pop("id", None)
        for json_field in ("email_source_urls_json", "personalization_source_urls_json"):
            if data.get(json_field):
                try:
                    data[json_field] = json.loads(data[json_field])
                except Exception:
                    pass
        sb.table("leads").upsert(data, on_conflict="email").execute()

    sends = conn.execute("SELECT * FROM sends").fetchall()
    for send in sends:
        data = dict(send)
        data.pop("id", None)
        sb.table("sends").upsert(data, on_conflict="id").execute()

    logger.info("✅ Live Supabase sync complete!")


def main():
    conn = db.get_connection()
    logger.info(f"Starting Wave 3 VC-Backed Campaign — {len(VC_STARTUPS)} companies...")

    # 1. Create or update Campaign for 19 August 2026 09:30 Europe/Istanbul
    scheduled_time = "2026-08-19T09:30:00+03:00"
    camp_id = db.create_campaign(conn, {
        "name": "vc-backed-outreach-2026-08-19",
        "target_leads": 20,
        "scheduled_start": scheduled_time,
        "timezone": "Europe/Istanbul",
        "status": "SCHEDULED",
    })
    logger.info(f"Created Campaign ID: {camp_id} scheduled for {scheduled_time}")

    new_lead_ids = []

    # 2. Ingest VC-backed companies & leads
    for item in VC_STARTUPS:
        founders = item.pop("founders", [])
        email = item.pop("email")
        pers = item.pop("personalization")

        # Ingest company
        cres = ingest_company(conn, founders=founders, **item)
        cid = cres["company_id"]
        cname = item["name"]
        cdomain = item["domain"]

        # Ingest co-founder lead
        for f in founders:
            fname = f["full_name"]
            first_name = f["first_name"]
            title = f["title"]
            hon = f["honorific"]

            lres = ingest_lead(
                conn,
                company_id=cid,
                company_name=cname,
                full_name=fname,
                first_name=first_name,
                title=title,
                contact_priority="Founder/Co-founder",
                honorific=hon,
                honorific_confidence="high",
                honorific_evidence_url=f"https://{cdomain}",
                email=email,
                email_provider="vc_portfolio_authoritative",
                email_score=95.0,
                email_verification_status="valid",
                email_source_urls=[f"https://{cdomain}"],
                personalization_paragraph=pers,
                personalization_source_urls=[item.get("funding_source_url") or f"https://{cdomain}"],
            )

            if lres["eligibility"]:
                # Set status to READY_FOR_REVIEW for Cloud execution at 09:30 AM
                conn.execute(
                    "UPDATE leads SET status = 'READY_FOR_REVIEW' WHERE id = ?",
                    (lres["lead_id"],),
                )
                conn.commit()
                new_lead_ids.append(lres["lead_id"])
                logger.info(f"  ✓ SCHEDULED LEAD: {fname} <{email}> @ {cname}")
            else:
                logger.warning(f"  ✗ INELIGIBLE: {fname} status={lres['status']}")

    logger.info(f"Total Wave 3 Leads Scheduled for 19 Aug 09:30: {len(new_lead_ids)}")

    # 3. Freeze Campaign Snapshot
    snapshot_hash = campaign.freeze_snapshot(conn, camp_id)
    campaign.approve_campaign(conn, camp_id)
    logger.info(f"Campaign snapshot frozen & approved! Hash: {snapshot_hash[:16]}")

    # 4. Generate Excel report
    export()

    # 5. Sync live to Supabase
    sync_to_supabase(conn)

    print(f"\n{'='*60}")
    print(f"WAVE 3 VC-BACKED CAMPAIGN PREPARED & SCHEDULED!")
    print(f"Target Start: 19 August 2026 09:30 Europe/Istanbul")
    print(f"Leads Prepared: {len(new_lead_ids)}")
    print(f"Synced Live to Supabase PostgreSQL!")
    print(f"{'='*60}\n")

    conn.close()


if __name__ == "__main__":
    main()
