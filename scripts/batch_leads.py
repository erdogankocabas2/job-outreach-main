#!/usr/bin/env python3
"""Batch ingest leads for all OUTREACH companies.

This script:
1. Creates lead records for researched contacts
2. Calls Hunter API to find/verify emails
3. Sets honorific
4. Writes personalization
5. Renders email using the locked template
"""

import json
import sys
import os
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

from src import db
from src.research import ingest_lead
from src import hunter, apollo

# ── Lead data: researched contacts for each OUTREACH company ──────────
# Contact priority: Founder/Co-founder → Chief of Staff → People/HR → Head of Growth/Product/BD
# Honorific from public evidence. Gender uncertain → NEEDS_GENDER_REVIEW

LEADS = [
    # ── Lucida AI ──────────────────────────────────────────────────────
    {
        "company_domain": "lucida.ai",
        "full_name": "Mustafa Girgin",
        "first_name": "Mustafa",
        "title": "Co-founder & CEO",
        "contact_priority": "Founder/Co-founder",
        "honorific": "Bey",
        "honorific_confidence": "high",
        "honorific_evidence_url": "https://mobidictum.com",
        "personalization_paragraph": "Coensio'nun Kariyer.net tarafından satın alınmasının ardından Lucida AI ile konuşma tabanlı yapay zeka alanında 3 milyondan fazla kullanıcıya ulaşmanız",
        "personalization_source_urls": ["https://mobidictum.com", "https://slator.com"],
    },
    {
        "company_domain": "lucida.ai",
        "full_name": "Mustafa Sait Demirci",
        "first_name": "Mustafa Sait",
        "title": "Co-founder",
        "contact_priority": "Founder/Co-founder",
        "honorific": "Bey",
        "honorific_confidence": "high",
        "honorific_evidence_url": "https://slator.com",
        "personalization_paragraph": "Lucida AI'ın Speech Language Model teknolojisiyle 150'den fazla ülkede gerçek zamanlı İngilizce koçluk sunması",
        "personalization_source_urls": ["https://slator.com", "https://tech.eu"],
    },
    # ── kayIQ.ai ──────────────────────────────────────────────────────
    {
        "company_domain": "kayiq.ai",
        "full_name": "Tolga Özel",
        "first_name": "Tolga",
        "title": "Founder & Head of Product Strategy",
        "contact_priority": "Founder/Co-founder",
        "honorific": "Bey",
        "honorific_confidence": "high",
        "honorific_evidence_url": "https://kayiq.ai",
        "personalization_paragraph": "kayIQ.ai'ın otonom yapay zeka ajanlarıyla yazılım test süreçlerini otomatikleştirmesi ve özellikle finans ve telekomünikasyon sektörlerindeki müşteri odağı",
        "personalization_source_urls": ["https://kayiq.ai", "https://dailysabah.com"],
    },
    {
        "company_domain": "kayiq.ai",
        "full_name": "Kubilay Şahhüseyinoğlu",
        "first_name": "Kubilay",
        "title": "Founder & Head of Customer Success",
        "contact_priority": "Founder/Co-founder",
        "honorific": "Bey",
        "honorific_confidence": "high",
        "honorific_evidence_url": "https://kayiq.ai",
        "personalization_paragraph": "kayIQ.ai'ın Agentic AI mimarisiyle test tasarımı ve bakımını tam otonom hale getiren yaklaşımı",
        "personalization_source_urls": ["https://kayiq.ai"],
    },
    # ── Novus ─────────────────────────────────────────────────────────
    {
        "company_domain": "novus.team",
        "full_name": "Egehan Asad",
        "first_name": "Egehan",
        "title": "Co-Founder & CEO",
        "contact_priority": "Founder/Co-founder",
        "honorific": "Bey",
        "honorific_confidence": "high",
        "honorific_evidence_url": "https://fundediq.co",
        "personalization_paragraph": "Novus'un LLM tabanlı AI agent orkestrasyon platformuyla kurumsal iş akışlarını dönüştürmesi ve Yapay Zeka Fabrikası'ndan aldığınız yatırım",
        "personalization_source_urls": ["https://fundediq.co"],
    },
    {
        "company_domain": "novus.team",
        "full_name": "Vorga Can",
        "first_name": "Vorga",
        "title": "Co-Founder & CRO",
        "contact_priority": "Founder/Co-founder",
        "honorific": "Bey",
        "honorific_confidence": "high",
        "honorific_evidence_url": "https://fundediq.co",
        "personalization_paragraph": "Novus'un yapay zeka ajanları ile enterprise workflow otomasyonundaki vizyonu",
        "personalization_source_urls": ["https://fundediq.co"],
    },
    # ── Syntonym ──────────────────────────────────────────────────────
    {
        "company_domain": "syntonym.io",
        "full_name": "Batuhan Ozcan",
        "first_name": "Batuhan",
        "title": "Founder",
        "contact_priority": "Founder/Co-founder",
        "honorific": "Bey",
        "honorific_confidence": "high",
        "honorific_evidence_url": "https://fundediq.co",
        "personalization_paragraph": "Syntonym'un generative AI ile yüz anonimleştirme yaparken analitik metrikleri koruyan GDPR/KVKK uyumlu çözümü",
        "personalization_source_urls": ["https://fundediq.co"],
    },
    # ── Buluttan ──────────────────────────────────────────────────────
    {
        "company_domain": "buluttan.com",
        "full_name": "Eren Kısmet",
        "first_name": "Eren",
        "title": "Co-Founder",
        "contact_priority": "Founder/Co-founder",
        "honorific": "Bey",
        "honorific_confidence": "high",
        "honorific_evidence_url": "https://buluttan.com",
        "personalization_paragraph": "Buluttan'ın Türkiye'nin ilk özel meteoroloji şirketi olarak yapay zeka tabanlı hiper-lokal hava tahminleriyle enerji ve lojistik sektörlerine sunduğu çözümler",
        "personalization_source_urls": ["https://buluttan.com"],
    },
    {
        "company_domain": "buluttan.com",
        "full_name": "Burçin Kısmet",
        "first_name": "Burçin",
        "title": "Co-Founder",
        "contact_priority": "Founder/Co-founder",
        "honorific": "Bey",
        "honorific_confidence": "high",
        "honorific_evidence_url": "https://buluttan.com",
        "personalization_paragraph": "Buluttan'ın AI tabanlı hava zekası platformuyla yenilenebilir enerji ve havacılık sektörlerindeki büyümesi",
        "personalization_source_urls": ["https://buluttan.com"],
    },
    # ── VenueX ────────────────────────────────────────────────────────
    {
        "company_domain": "venuex.co",
        "full_name": "Kursad Arman",
        "first_name": "Kursad",
        "title": "Co-Founder & CEO",
        "contact_priority": "Founder/Co-founder",
        "honorific": "Bey",
        "honorific_confidence": "high",
        "honorific_evidence_url": "https://venuex.co",
        "personalization_paragraph": "VenueX'in AI ajanlarıyla dijital reklam harcamalarını fiziksel mağaza satışlarına bağlayan platformu ve Dubai-Riyad'a genişlemeniz",
        "personalization_source_urls": ["https://venuex.co", "https://fundediq.co"],
    },
    # ── Co-One ────────────────────────────────────────────────────────
    {
        "company_domain": "co-one.co",
        "full_name": "Arman Kayhan",
        "first_name": "Arman",
        "title": "Co-Founder",
        "contact_priority": "Founder/Co-founder",
        "honorific": "Bey",
        "honorific_confidence": "high",
        "honorific_evidence_url": "https://co-one.co",
        "personalization_paragraph": "Co-One'ın e-ticaret ve bankacılık için geliştirdiği 'real-world ready' AI ajanları ve Avrupa-MENA pazarlarındaki büyümesi",
        "personalization_source_urls": ["https://co-one.co"],
    },
    {
        "company_domain": "co-one.co",
        "full_name": "Mert Menekşe",
        "first_name": "Mert",
        "title": "Co-Founder",
        "contact_priority": "Founder/Co-founder",
        "honorific": "Bey",
        "honorific_confidence": "high",
        "honorific_evidence_url": "https://co-one.co",
        "personalization_paragraph": "Co-One'ın AI ajanlarıyla e-ticaret ve bankacılık sektörlerinde veri altyapısı çözümleri sunması",
        "personalization_source_urls": ["https://co-one.co"],
    },
    # ── SuperGears Games ──────────────────────────────────────────────
    {
        "company_domain": "supergears.games",
        "full_name": "Yasin Demirden",
        "first_name": "Yasin",
        "title": "Co-Founder",
        "contact_priority": "Founder/Co-founder",
        "honorific": "Bey",
        "honorific_confidence": "high",
        "honorific_evidence_url": "https://supergears.games",
        "personalization_paragraph": "ZULA ve Kabus 22 gibi ikonik oyunların ardından Racing Kingdom ile mobil oyun alanında 'En İyi Mobil Oyun' ödülü almanız",
        "personalization_source_urls": ["https://supergears.games", "https://gamespress.com"],
    },
    {
        "company_domain": "supergears.games",
        "full_name": "Yakup Demirden",
        "first_name": "Yakup",
        "title": "Co-Founder",
        "contact_priority": "Founder/Co-founder",
        "honorific": "Bey",
        "honorific_confidence": "high",
        "honorific_evidence_url": "https://supergears.games",
        "personalization_paragraph": "20 yılı aşkın oyun geliştirme deneyiminizle SuperGears'ın Racing Kingdom'ı milyonlarca oyuncuya ulaştırması ve KRAFTON'un stratejik yatırımı",
        "personalization_source_urls": ["https://supergears.games", "https://egirisim.com"],
    },
    # ── Bold Games ────────────────────────────────────────────────────
    {
        "company_domain": "boldgames.co",
        "full_name": "Ulaş Mergen",
        "first_name": "Ulaş",
        "title": "CEO & Founder",
        "contact_priority": "Founder/Co-founder",
        "honorific": "Bey",
        "honorific_confidence": "high",
        "honorific_evidence_url": "https://pocketgamer.biz",
        "personalization_paragraph": "Bigger Games, Dream Games ve Rollic gibi stüdyolardaki deneyiminizin ardından Bold Games ile Market Match'i geliştirmeniz ve $6M seed yatırım almanız",
        "personalization_source_urls": ["https://pocketgamer.biz", "https://arabfounders.net"],
    },
    {
        "company_domain": "boldgames.co",
        "full_name": "Atakan Tuğlu",
        "first_name": "Atakan",
        "title": "CMO & Co-Founder",
        "contact_priority": "Founder/Co-founder",
        "honorific": "Bey",
        "honorific_confidence": "high",
        "honorific_evidence_url": "https://pocketgamer.biz",
        "personalization_paragraph": "Bold Games'in 10 kişilik bir ekiple $6M seed yatırım alarak sort-puzzle türünde uzun ömürlü oyun deneyimleri yaratma vizyonu",
        "personalization_source_urls": ["https://pocketgamer.biz"],
    },
    # ── Circle Games ──────────────────────────────────────────────────
    {
        "company_domain": "circlegames.co",
        "full_name": "Göktürk Balıkçı",
        "first_name": "Göktürk",
        "title": "CEO & Co-Founder",
        "contact_priority": "Founder/Co-founder",
        "honorific": "Bey",
        "honorific_confidence": "high",
        "honorific_evidence_url": "https://a16z.com",
        "personalization_paragraph": "Üniversiteden tanıştığınız arkadaşlarınızla Gram Games ve Dream Games deneyiminin ardından Circle Games'i kurmanız ve a16z Speedrun ile BITKRAFT'tan $7.25M yatırım almanız",
        "personalization_source_urls": ["https://a16z.com", "https://mobidictum.com"],
    },
    {
        "company_domain": "circlegames.co",
        "full_name": "Mustafa Özdemir",
        "first_name": "Mustafa",
        "title": "CPO & Co-Founder",
        "contact_priority": "Founder/Co-founder",
        "honorific": "Bey",
        "honorific_confidence": "high",
        "honorific_evidence_url": "https://bitkraft.vc",
        "personalization_paragraph": "Circle Games'in Sort Express! ile casual puzzle alanındaki ürün vizyonu ve BITKRAFT liderliğindeki $7.25M yatırım turu",
        "personalization_source_urls": ["https://bitkraft.vc", "https://mobidictum.com"],
    },
    # ── Fuse Games ────────────────────────────────────────────────────
    {
        "company_domain": "fusegames.co",
        "full_name": "Akın Semih Şahan",
        "first_name": "Akın Semih",
        "title": "CEO & Co-Founder",
        "contact_priority": "Founder/Co-founder",
        "honorific": "Bey",
        "honorific_confidence": "high",
        "honorific_evidence_url": "https://webrazzi.com",
        "personalization_paragraph": "Fuse Games'in orijinal IP geliştirme odağıyla Griffin Gaming Partners liderliğinde $7M yatırım alması ve proprietary araçlar geliştirmesi",
        "personalization_source_urls": ["https://finsmes.com", "https://webrazzi.com"],
    },
    # ── Bigger Games ──────────────────────────────────────────────────
    {
        "company_domain": "biggergames.com",
        "full_name": "Hakan Ulvan",
        "first_name": "Hakan",
        "title": "CEO & Co-Founder",
        "contact_priority": "Founder/Co-founder",
        "honorific": "Bey",
        "honorific_confidence": "high",
        "honorific_evidence_url": "https://indexventures.com",
        "personalization_paragraph": "Peak Games'teki $1.8B'lık satış deneyiminizin ardından Bigger Games ile Goodwater Capital liderliğinde $25M Series A yatırım almanız",
        "personalization_source_urls": ["https://indexventures.com", "https://gamesbeat.com"],
    },
    {
        "company_domain": "biggergames.com",
        "full_name": "Erkan Gürel",
        "first_name": "Erkan",
        "title": "Co-Founder",
        "contact_priority": "Founder/Co-founder",
        "honorific": "Bey",
        "honorific_confidence": "high",
        "honorific_evidence_url": "https://gamizm.com",
        "personalization_paragraph": "Peak Games alumni olarak Bigger Games'in data-driven yaklaşımıyla Kitchen Masters'ı başarılı bir şekilde büyütmeniz",
        "personalization_source_urls": ["https://gamizm.com"],
    },
    # ── Agave Games ───────────────────────────────────────────────────
    {
        "company_domain": "agavegames.com",
        "full_name": "Alper Oner",
        "first_name": "Alper",
        "title": "CEO",
        "contact_priority": "Founder/Co-founder",
        "honorific": "Bey",
        "honorific_confidence": "high",
        "honorific_evidence_url": "https://fundediq.co",
        "personalization_paragraph": "Agave Games'in Find the Cat ile casual puzzle alanındaki başarısı ve toplam $25M yatırımla sağlanan güçlü büyüme",
        "personalization_source_urls": ["https://fundediq.co"],
    },
    # ── Grand Games ───────────────────────────────────────────────────
    {
        "company_domain": "grandgames.co",
        "full_name": "Bekir Batuhan Çelebi",
        "first_name": "Batuhan",
        "title": "Co-Founder",
        "contact_priority": "Founder/Co-founder",
        "honorific": "Bey",
        "honorific_confidence": "high",
        "honorific_evidence_url": "https://mobidictum.com",
        "personalization_paragraph": "Grand Games'in kuruluşundan sadece 9 ay sonra $30M Series A alması ve toplam $105M'a ulaşan olağanüstü büyüme hikayesi",
        "personalization_source_urls": ["https://mobidictum.com"],
    },
    {
        "company_domain": "grandgames.co",
        "full_name": "Mehmet Çalım",
        "first_name": "Mehmet",
        "title": "Co-Founder",
        "contact_priority": "Founder/Co-founder",
        "honorific": "Bey",
        "honorific_confidence": "high",
        "honorific_evidence_url": "https://mobidictum.com",
        "personalization_paragraph": "Grand Games'in Magic Sort! ve Car Match oyunlarıyla ~14 kişilik ekiple $105M yatırım çekmesi",
        "personalization_source_urls": ["https://mobidictum.com"],
    },
    # ── Wask ──────────────────────────────────────────────────────────
    {
        "company_domain": "wask.co",
        "full_name": "Mert Akgün",
        "first_name": "Mert",
        "title": "CEO & Founder",
        "contact_priority": "Founder/Co-founder",
        "honorific": "Bey",
        "honorific_confidence": "high",
        "honorific_evidence_url": "https://wask.co",
        "personalization_paragraph": "Wask'ın yapay zeka destekli dijital pazarlama platformuyla Google ve Meta reklamlarını otomatik olarak optimize etmesi",
        "personalization_source_urls": ["https://wask.co"],
    },
    # ── CBOT ──────────────────────────────────────────────────────────
    {
        "company_domain": "cbot.ai",
        "full_name": "Cemal Büyükgökçesu",
        "first_name": "Cemal",
        "title": "CEO & Founder",
        "contact_priority": "Founder/Co-founder",
        "honorific": "Bey",
        "honorific_confidence": "high",
        "honorific_evidence_url": "https://cbot.ai",
        "personalization_paragraph": "CBOT'un doğal dil işleme teknolojisiyle enterprise chatbot ve sanal asistan çözümleri sunması",
        "personalization_source_urls": ["https://cbot.ai"],
    },
    # ── B2Metric ──────────────────────────────────────────────────────
    {
        "company_domain": "b2metric.com",
        "full_name": "Erdal Koca",
        "first_name": "Erdal",
        "title": "CEO & Founder",
        "contact_priority": "Founder/Co-founder",
        "honorific": "Bey",
        "honorific_confidence": "high",
        "honorific_evidence_url": "https://b2metric.com",
        "personalization_paragraph": "B2Metric'in AutoML yaklaşımıyla müşteri davranışı tahmini ve iş zekası alanında sunduğu çözümler",
        "personalization_source_urls": ["https://b2metric.com"],
    },
    # ── Vispera ───────────────────────────────────────────────────────
    {
        "company_domain": "vispera.co",
        "full_name": "Aytül Erçil",
        "first_name": "Aytül",
        "title": "Founder & CEO",
        "contact_priority": "Founder/Co-founder",
        "honorific": "Hanım",
        "honorific_confidence": "high",
        "honorific_evidence_url": "https://vispera.co",
        "personalization_paragraph": "Vispera'nın bilgisayar görüsü ve yapay zeka ile perakende raf analitiğinde lider konuma gelmesi ve uluslararası müşteri portföyü",
        "personalization_source_urls": ["https://vispera.co"],
    },
    # ── Storyly ───────────────────────────────────────────────────────
    {
        "company_domain": "storyly.io",
        "full_name": "Levent Tüfekçi",
        "first_name": "Levent",
        "title": "CEO & Co-Founder",
        "contact_priority": "Founder/Co-founder",
        "honorific": "Bey",
        "honorific_confidence": "high",
        "honorific_evidence_url": "https://storyly.io",
        "personalization_paragraph": "Storyly'nin interaktif stories formatıyla mobil uygulama kullanıcı etkileşimini artıran SaaS platformu ve uluslararası müşteri tabanı",
        "personalization_source_urls": ["https://storyly.io"],
    },
    # ── Segmentify ────────────────────────────────────────────────────
    {
        "company_domain": "segmentify.com",
        "full_name": "Murat Soysal",
        "first_name": "Murat",
        "title": "CEO & Co-Founder",
        "contact_priority": "Founder/Co-founder",
        "honorific": "Bey",
        "honorific_confidence": "high",
        "honorific_evidence_url": "https://segmentify.com",
        "personalization_paragraph": "Segmentify'ın yapay zeka destekli gerçek zamanlı ürün önerileriyle e-ticaret kişiselleştirmesindeki başarısı",
        "personalization_source_urls": ["https://segmentify.com"],
    },
    # ── OctoXLabs ─────────────────────────────────────────────────────
    {
        "company_domain": "octoxlabs.com",
        "full_name": "Yavuz Han",
        "first_name": "Yavuz",
        "title": "CEO & Founder",
        "contact_priority": "Founder/Co-founder",
        "honorific": "Bey",
        "honorific_confidence": "high",
        "honorific_evidence_url": "https://octoxlabs.com",
        "personalization_paragraph": "OctoXLabs'ın yapay zeka destekli CAASM platformuyla siber güvenlik varlık yönetiminde sunduğu çözümler",
        "personalization_source_urls": ["https://octoxlabs.com"],
    },
    # ── TeamSec ───────────────────────────────────────────────────────
    {
        "company_domain": "teamsec.com",
        "full_name": "Sertaç Özpınar",
        "first_name": "Sertaç",
        "title": "CEO & Founder",
        "contact_priority": "Founder/Co-founder",
        "honorific": "Bey",
        "honorific_confidence": "high",
        "honorific_evidence_url": "https://teamsec.com",
        "personalization_paragraph": "TeamSec'in AI destekli Securitization-as-a-Service platformuyla $7.6M yatırım alması ve finans kurumlarına sunduğu regtech çözümü",
        "personalization_source_urls": ["https://teamsec.com", "https://fundediq.co"],
    },
]


def main():
    """Ingest all leads and attempt Hunter email discovery."""
    conn = db.get_connection()

    # Build domain → company_id mapping
    companies = db.get_all_companies(conn)
    domain_map = {c["domain"]: c for c in companies}

    print(f"\n{'='*60}")
    print(f"LEAD INGESTION: {len(LEADS)} leads")
    print(f"{'='*60}\n")

    # Check Hunter availability
    hunter_available = True
    try:
        hunter._get_api_key()
    except RuntimeError:
        hunter_available = False
        print("⚠️  HUNTER_API_KEY not set — skipping email discovery\n")

    apollo_available = apollo.is_available()
    if apollo_available:
        print("✓  Apollo API available as fallback\n")

    stats = {"eligible": 0, "email_found": 0, "email_not_found": 0, "needs_review": 0, "errors": 0}

    for i, lead_data in enumerate(LEADS):
        domain = lead_data.pop("company_domain")
        company = domain_map.get(domain)

        if not company:
            print(f"  ⚠️  Company not found for domain {domain}")
            stats["errors"] += 1
            continue

        company_id = company["id"]
        company_name = company["name"]

        # Try Hunter email finder
        email = None
        email_provider = None
        email_score = None
        email_verification_status = None

        if hunter_available:
            # Parse name parts
            name_parts = lead_data["full_name"].split()
            first = name_parts[0]
            last = name_parts[-1] if len(name_parts) > 1 else ""

            try:
                result = hunter.find_email(domain, first, last)
                if result.email and hunter.is_eligible(result):
                    email = result.email
                    email_provider = "hunter"
                    email_score = result.score
                    email_verification_status = "valid"
                    stats["email_found"] += 1
                elif result.email:
                    # Found but not eligible — try verifying
                    verify_result = hunter.verify_email(result.email)
                    if hunter.is_eligible(verify_result):
                        email = verify_result.email
                        email_provider = "hunter"
                        email_score = verify_result.score
                        email_verification_status = verify_result.status
                        stats["email_found"] += 1
                    else:
                        email = result.email
                        email_provider = "hunter"
                        email_score = result.score
                        email_verification_status = result.status or "unverified"
                        stats["email_not_found"] += 1
                else:
                    stats["email_not_found"] += 1

                # Rate limit
                time.sleep(1)

            except Exception as e:
                print(f"  ⚠️  Hunter error for {lead_data['full_name']}: {e}")
                stats["errors"] += 1

        # Apollo fallback if no email found
        if not email and apollo_available:
            try:
                name_parts = lead_data["full_name"].split()
                first = name_parts[0]
                last = name_parts[-1] if len(name_parts) > 1 else ""
                
                aresult = apollo.find_person_email(first, last, domain)
                if aresult.email and apollo.is_eligible(aresult):
                    email = aresult.email
                    email_provider = "apollo"
                    email_score = 90
                    email_verification_status = "valid"
                    stats["email_found"] += 1
                
                time.sleep(0.5)
            except Exception as e:
                print(f"  ⚠️  Apollo error for {lead_data['full_name']}: {e}")

        # Ingest the lead
        result = ingest_lead(
            conn,
            company_id=company_id,
            company_name=company_name,
            email=email,
            email_provider=email_provider,
            email_score=email_score,
            email_verification_status=email_verification_status,
            email_source_urls=[f"https://api.hunter.io"] if email_provider == "hunter" else [],
            **lead_data,
        )

        status_icon = "✓" if result["eligibility"] else "✗"
        print(
            f"  [{status_icon}] {lead_data['full_name']:30s} @ {company_name:20s} "
            f"email={'✓' if email else '✗':3s} status={result['status']}"
        )

        if result["eligibility"]:
            stats["eligible"] += 1

    print(f"\n{'='*60}")
    print(f"SUMMARY:")
    print(f"  Eligible:       {stats['eligible']}")
    print(f"  Emails found:   {stats['email_found']}")
    print(f"  Emails missing: {stats['email_not_found']}")
    print(f"  Needs review:   {stats['needs_review']}")
    print(f"  Errors:         {stats['errors']}")
    print(f"{'='*60}\n")

    conn.close()


if __name__ == "__main__":
    main()
