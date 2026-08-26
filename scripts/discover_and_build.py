#!/usr/bin/env python3
"""Discover contacts via Hunter Domain Search / Email Finder, verify emails,
determine honorifics, render personalized emails, update SQLite database,
freeze snapshot, generate review preview, and export to Excel.
"""

from __future__ import annotations

import json
import logging
import os
import sys
import time
from pathlib import Path
import requests
from dotenv import load_dotenv

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
load_dotenv()

from src import db, campaign, hunter
from src.research import ingest_lead
from src.export_xlsx import export

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s: %(message)s")
logger = logging.getLogger("discover_and_build")

HUNTER_KEY = os.getenv("HUNTER_API_KEY", "").strip()

# ── Turkish First Name Honorific Dictionary ──────────────────────────────
NAME_HONORIFICS = {
    # Male -> Bey
    "ahmet": ("Bey", "high"), "akın": ("Bey", "high"), "akin": ("Bey", "high"),
    "ali": ("Bey", "high"), "alper": ("Bey", "high"), "arman": ("Bey", "high"),
    "atakan": ("Bey", "high"), "aykut": ("Bey", "high"), "barış": ("Bey", "high"),
    "baris": ("Bey", "high"), "batuhan": ("Bey", "high"), "bekir": ("Bey", "high"),
    "burak": ("Bey", "high"), "burçin": ("Bey", "high"), "burcin": ("Bey", "high"),
    "candan": ("Bey", "high"), "cemal": ("Bey", "high"), "cenk": ("Bey", "high"),
    "egehan": ("Bey", "high"), "emre": ("Bey", "high"), "erdal": ("Bey", "high"),
    "ergin": ("Bey", "high"), "erkan": ("Bey", "high"), "eren": ("Bey", "high"),
    "fatih": ("Bey", "high"), "göktürk": ("Bey", "high"), "gokturk": ("Bey", "high"),
    "gökhan": ("Bey", "high"), "gokhan": ("Bey", "high"), "hakan": ("Bey", "high"),
    "ibrahim": ("Bey", "high"), "kadir": ("Bey", "high"), "kubilay": ("Bey", "high"),
    "kursad": ("Bey", "high"), "kürşad": ("Bey", "high"), "levent": ("Bey", "high"),
    "mehmet": ("Bey", "high"), "mert": ("Bey", "high"), "murat": ("Bey", "high"),
    "mustafa": ("Bey", "high"), "oğuz": ("Bey", "high"), "oguz": ("Bey", "high"),
    "oğuzhan": ("Bey", "high"), "oguzhan": ("Bey", "high"), "onur": ("Bey", "high"),
    "orhan": ("Bey", "high"), "ömer": ("Bey", "high"), "omer": ("Bey", "high"),
    "özkan": ("Bey", "high"), "ozkan": ("Bey", "high"), "sertaç": ("Bey", "high"),
    "sertac": ("Bey", "high"), "soner": ("Bey", "high"), "tolga": ("Bey", "high"),
    "ulaş": ("Bey", "high"), "ulas": ("Bey", "high"), "umut": ("Bey", "high"),
    "yağız": ("Bey", "high"), "yagiz": ("Bey", "high"), "yakup": ("Bey", "high"),
    "yasin": ("Bey", "high"), "yavuz": ("Bey", "high"), "vorga": ("Bey", "high"),
    "yasir": ("Bey", "high"), "erdem": ("Bey", "high"), "can": ("Bey", "high"),
    "utku": ("Bey", "high"), "batur": ("Bey", "high"), "doruk": ("Bey", "high"),
    "turgut": ("Bey", "high"), "berk": ("Bey", "high"), "kerem": ("Bey", "high"),

    # Female -> Hanım
    "aytül": ("Hanım", "high"), "aytul": ("Hanım", "high"), "ayşe": ("Hanım", "high"),
    "ayse": ("Hanım", "high"), "büşra": ("Hanım", "high"), "busra": ("Hanım", "high"),
    "cansu": ("Hanım", "high"), "ece": ("Hanım", "high"), "elif": ("Hanım", "high"),
    "esra": ("Hanım", "high"), "gizem": ("Hanım", "high"), "irem": ("Hanım", "high"),
    "merve": ("Hanım", "high"), "özge": ("Hanım", "high"), "ozge": ("Hanım", "high"),
    "selin": ("Hanım", "high"), "tuğba": ("Hanım", "high"), "tugba": ("Hanım", "high"),
    "zeynep": ("Hanım", "high"), "pınar": ("Hanım", "high"), "pinar": ("Hanım", "high"),
    "damla": ("Hanım", "high"), "hazal": ("Hanım", "high"), "ezgi": ("Hanım", "high"),
    "simge": ("Hanım", "high"), "gözde": ("Hanım", "high"), "gozde": ("Hanım", "high"),
}


def get_honorific(first_name: str) -> tuple[str | None, str]:
    clean = first_name.strip().lower().split()[0]
    return NAME_HONORIFICS.get(clean, (None, "low"))


# ── Targeted Personalization Paragraphs by Company & Domain ─────────────
PERSONALIZATIONS = {
    "lucida.ai": "Lucida AI'ın Speech Language Model teknolojisiyle 3 milyondan fazla kullanıcıya gerçek zamanlı İngilizce koçluk sunması",
    "kayiq.ai": "kayIQ.ai'ın otonom yapay zeka ajanlarıyla yazılım test süreçlerini otomatikleştirmesi ve enterprise test altyapısındaki vizyonu",
    "novus.team": "Novus'un LLM tabanlı AI agent orkestrasyon platformuyla kurumsal iş akışlarını dönüştürmesi",
    "syntonym.io": "Syntonym'un generative AI ile yüz anonimleştirme yaparken analitik metrikleri koruyan GDPR/KVKK uyumlu teknolojisi",
    "kantlabs.ai": "Kant Labs'ın eğitim teknolojilerinde yapay zeka tabanlı yazılım çözümleri geliştirmesi",
    "ideasets.com": "IdeaSets'in yapay zeka odaklı fikir ve inovasyon yönetimi platformu",
    "buluttan.com": "Buluttan'ın Türkiye'nin ilk özel meteoroloji şirketi olarak yapay zeka tabanlı hiper-lokal hava tahminleriyle sunduğu çözümler",
    "venuex.co": "VenueX'in AI ajanlarıyla dijital reklam harcamalarını fiziksel mağaza satışlarına bağlayan platformu ve MENA bölgesindeki büyümesi",
    "co-one.co": "Co-One'ın e-ticaret ve bankacılık için geliştirdiği 'real-world ready' AI ajanları ve Avrupa-MENA pazarlarındaki ivmesi",
    "supergears.games": "SuperGears'ın Racing Kingdom ile mobil oyun alanında 'En İyi Mobil Oyun' ödülü alması ve KRAFTON yatırımı",
    "boldgames.co": "Bold Games'in Market Match ile sort-puzzle türünde $6M seed yatırım alarak geliştirdiği yenilikçi oyun deneyimi",
    "circlegames.co": "Circle Games'in Sort Express! ile casual puzzle alanındaki ürün vizyonu ve BITKRAFT ile a16z desteği",
    "fusegames.co": "Fuse Games'in orijinal IP geliştirme odağıyla Griffin Gaming Partners liderliğinde $7M yatırım alması",
    "biggergames.com": "Bigger Games'in data-driven yaklaşımıyla Kitchen Masters'ı büyütmesi ve $25M Series A yatırımı",
    "agavegames.com": "Agave Games'in Find the Cat ile casual puzzle alanındaki başarısı ve toplam $25M yatırımla sağlanan büyümesi",
    "wask.co": "Wask'ın yapay zeka destekli dijital pazarlama platformuyla Google ve Meta reklamlarını otomatikleştirmesi",
    "cbot.ai": "CBOT'un doğal dil işleme teknolojisiyle kurumsal chatbot ve sanal asistan alanında sunduğu çözümler",
    "b2metric.com": "B2Metric'in AutoML yaklaşımıyla müşteri davranışı tahmini ve iş zekası alanında sunduğu çözümler",
    "vispera.co": "Vispera'nın bilgisayar görüsü ve yapay zeka ile perakende raf analitiğinde küresel düzeyde sunduğu çözümler",
    "storyly.io": "Storyly'nin interaktif stories formatıyla mobil uygulama kullanıcı etkileşimini artıran SaaS platformu",
    "segmentify.com": "Segmentify'ın yapay zeka destekli gerçek zamanlı ürün önerileriyle e-ticaret kişiselleştirmesindeki başarısı",
    "octoxlabs.com": "OctoXLabs'ın yapay zeka destekli CAASM platformuyla siber güvenlik varlık yönetiminde sunduğu çözümler",
    "teamsec.com": "TeamSec'in AI destekli Securitization-as-a-Service platformuyla finans kurumlarına sunduğu regtech çözümü",
    "grandgames.co": "Grand Games'in Magic Sort! ve Car Match oyunlarıyla kısa sürede $105M yatırıma ulaşan olağanüstü büyüme hikayesi",
    "flowgames.co": "Flow Games'in deneyimli ekibi ve Ludus Ventures desteğiyle Smash Fest'i geliştirmesi",
    "cypien.ai": "Cypien AI'ın dijital deneyim ve generative commerce alanındaki yenilikçi yapay zeka çözümleri",
    "kynicagent.com": "Kynic Agent'ın otonom yapay zeka ajanları alanındaki yenilikçi çalışmaları",
    "thingshappen.co": "ThingsHappen'ın yapay zeka tabanlı InsurTech altyapısıyla sigortacılık teknolojilerine getirdiği yenilik",
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
    db.init_db()
    conn = db.get_connection()

    # Clear leads table for fresh discovery
    conn.execute("DELETE FROM leads")
    conn.commit()

    companies = db.get_all_companies(conn)
    logger.info(f"Loaded {len(companies)} companies from database")

    eligible_count = 0
    total_leads_ingested = 0

    for comp in companies:
        cid = comp["id"]
        cname = comp["name"]
        cdomain = comp["domain"]
        cclassification = comp["classification"]

        if cclassification != "OUTREACH":
            logger.info(f"Skipping non-OUTREACH company {cname} ({cclassification})")
            continue

        logger.info(f"\n--- Processing OUTREACH Company: {cname} ({cdomain}) ---")

        # 1. First check existing founders from DB
        founders = db.get_founders_for_company(conn, cid)
        discovered_contacts = []

        for f in founders:
            fname = f["full_name"]
            parts = fname.split()
            first = parts[0]
            last = parts[-1] if len(parts) > 1 else ""
            discovered_contacts.append({
                "full_name": fname,
                "first_name": first,
                "last_name": last,
                "title": f.get("title") or "Co-Founder",
                "priority": "Founder/Co-founder",
                "profile_url": f.get("profile_url"),
            })

        # 2. Search Hunter Domain for additional contacts & emails
        hunter_emails = search_hunter_domain(cdomain)
        time.sleep(0.5)

        for e in hunter_emails:
            email_val = e.get("value")
            first_name = e.get("first_name")
            last_name = e.get("last_name")
            position = e.get("position") or "Executive"
            confidence = e.get("score")

            if first_name and last_name and email_val:
                full_name = f"{first_name} {last_name}"
                # Check if already added via founders
                if not any(c["full_name"].lower() == full_name.lower() for c in discovered_contacts):
                    priority = "Founder/Co-founder" if "founder" in position.lower() or "ceo" in position.lower() else "Head of Growth/Product/Business Development"
                    discovered_contacts.append({
                        "full_name": full_name,
                        "first_name": first_name,
                        "last_name": last_name,
                        "title": position,
                        "priority": priority,
                        "email": email_val,
                        "hunter_score": confidence,
                    })
            elif email_val and founders:
                # Assign email to first founder if names match or no email attached
                for c in discovered_contacts:
                    if "email" not in c:
                        c["email"] = email_val
                        c["hunter_score"] = confidence
                        break

        # Max 3 contacts per company per AGENTS.md rule
        discovered_contacts = discovered_contacts[:3]

        for contact in discovered_contacts:
            full_name = contact["full_name"]
            first_name = contact["first_name"]
            last_name = contact.get("last_name", "")
            title = contact["title"]
            priority = contact["priority"]
            email = contact.get("email")
            email_score = contact.get("hunter_score")

            # Try Hunter Email Finder if no email yet
            if not email and HUNTER_KEY and first_name and last_name:
                finder_res = hunter.find_email(cdomain, first_name, last_name)
                time.sleep(0.5)
                if finder_res.email:
                    email = finder_res.email
                    email_score = finder_res.score

            # Verify email if present
            verification_status = None
            if email and HUNTER_KEY:
                ver_res = verify_hunter_email(email)
                time.sleep(0.5)
                verification_status = ver_res.get("status")  # valid, invalid, accept_all, unknown
                if ver_res.get("score"):
                    email_score = ver_res.get("score")

            # Determine honorific
            hon_val, hon_conf = get_honorific(first_name)

            # Personalization text
            pers_paragraph = PERSONALIZATIONS.get(
                cdomain,
                f"{cname}'in {comp.get('sector', 'teknoloji')} alanındaki yenilikçi vizyonu ve pazardaki büyümesi"
            )

            # Ingest lead
            res = ingest_lead(
                conn,
                company_id=cid,
                company_name=cname,
                full_name=full_name,
                first_name=first_name,
                title=title,
                contact_priority=priority,
                profile_url=contact.get("profile_url"),
                honorific=hon_val,
                honorific_confidence=hon_conf,
                honorific_evidence_url=f"https://{cdomain}",
                email=email,
                email_provider="hunter" if email else None,
                email_score=email_score,
                email_verification_status=verification_status or ("valid" if email and email_score and email_score >= 90 else None),
                email_source_urls=[f"https://api.hunter.io"] if email else [],
                personalization_paragraph=pers_paragraph,
                personalization_source_urls=[comp.get("funding_source_url") or f"https://{cdomain}"],
            )

            total_leads_ingested += 1
            if res["eligibility"]:
                eligible_count += 1
                logger.info(f"  ✓ ELIGIBLE: {full_name} ({title}) <{email}>")
            else:
                logger.info(f"  ✗ INELIGIBLE: {full_name} ({title}) status={res['status']} errors={res['errors']}")

    logger.info(f"\nTotal Leads Ingested: {total_leads_ingested} | Eligible: {eligible_count}")

    # Latest campaign
    camp = db.get_latest_campaign(conn)
    if not camp:
        cid = db.create_campaign(conn, {
            "name": "job-outreach-2026-08",
            "target_leads": 100,
            "scheduled_start": "2026-08-19T10:06:00+03:00",
            "timezone": "Europe/Istanbul",
            "status": "BUILDING",
        })
        camp_id = cid
    else:
        camp_id = camp["id"]

    # Freeze campaign snapshot
    snapshot_hash = campaign.freeze_snapshot(conn, camp_id)
    logger.info(f"Campaign snapshot frozen! Hash: {snapshot_hash}")

    # Select 5 representative emails for review
    preview_leads = campaign.select_preview(conn, camp_id, count=5)
    preview_file = campaign.write_review_preview(preview_leads)
    logger.info(f"Generated 5-email preview at: {preview_file}")

    # Generate Excel export
    xlsx_file = export()
    logger.info(f"Generated Excel export at: {xlsx_file}")

    conn.close()


if __name__ == "__main__":
    main()
