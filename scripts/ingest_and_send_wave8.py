#!/usr/bin/env python3
"""Ingest Wave 8 companies and leads into DB, then dispatch carefully with 30s pacing."""

from __future__ import annotations

import logging
import os
import sys
import time
import sqlite3
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo
from dotenv import load_dotenv

load_dotenv()
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src import db, smtp_client
from src.export_xlsx import export

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s: %(message)s")
logger = logging.getLogger("wave8")

WAVE8_COMPANIES = [
    {
        "name": "Artlabs",
        "domain": "artlabs.ai",
        "sector": "AI / 3D eCommerce",
        "description": "E-ticaret ve markalar için 3D ve artırılmış gerçeklik (AR) yapay zeka platformu",
        "founders": [
            {"name": "Uğur Yekta Başak", "title": "Co-Founder & CEO", "university": "Boğaziçi Üniv.", "prev": "TechOne backed"},
            {"name": "Sercan Demircan", "title": "Co-Founder & COO", "university": "ODTÜ", "prev": "Artlabs"}
        ],
        "leads": [
            {
                "full_name": "Uğur Yekta Başak",
                "first_name": "Uğur",
                "honorific": "Bey",
                "role": "Co-Founder & CEO",
                "email": "ugur@artlabs.ai",
                "personalization": "Artlabs'ın yapay zeka ve 3D/AR teknolojisiyle e-ticaret markalarının dönüşüm oranlarını artıran yenilikçi platformu"
            },
            {
                "full_name": "Sercan Demircan",
                "first_name": "Sercan",
                "honorific": "Bey",
                "role": "Co-Founder & COO",
                "email": "sercan@artlabs.ai",
                "personalization": "Artlabs'ın küresel pazarda sanal deneme ve 3D ürün görselleştirme alanında yarattığı güçlü büyüme"
            }
        ]
    },
    {
        "name": "Prisync",
        "domain": "prisync.com",
        "sector": "SaaS / Pricing Intelligence",
        "description": "E-ticaret şirketleri için rakip fiyat takip ve dinamik fiyatlandırma SaaS platformu",
        "founders": [
            {"name": "Burç Tanır", "title": "Co-Founder & CEO", "university": "Boğaziçi Üniv.", "prev": "Collective Spark backed"},
            {"name": "Samet Atdağ", "title": "Co-Founder & CTO", "university": "ODTÜ", "prev": "Prisync"}
        ],
        "leads": [
            {
                "full_name": "Burç Tanır",
                "first_name": "Burç",
                "honorific": "Bey",
                "role": "Co-Founder & CEO",
                "email": "burc@prisync.com",
                "personalization": "Prisync'in 50'den fazla ülkede e-ticaret şirketlerinin karlılığını optimize eden dinamik fiyatlandırma başarısı"
            },
            {
                "full_name": "Samet Atdağ",
                "first_name": "Samet",
                "honorific": "Bey",
                "role": "Co-Founder & CTO",
                "email": "samet@prisync.com",
                "personalization": "Prisync'in küresel veri çekme ve fiyat analitiği alanındaki sağlam teknolojik altyapısı"
            }
        ]
    },
    {
        "name": "Kunduz",
        "domain": "kunduz.com",
        "sector": "EdTech / AI",
        "description": "Öğrenciler için 7/24 kişiselleştirilmiş soru çözüm ve eğitim yapay zeka platformu",
        "founders": [
            {"name": "Başar Başaran", "title": "Co-Founder & CEO", "university": "Boğaziçi Üniv.", "prev": "Y Combinator alumni"},
            {"name": "Melih Şener", "title": "Co-Founder & CTO", "university": "Boğaziçi Üniv.", "prev": "Y Combinator alumni"}
        ],
        "leads": [
            {
                "full_name": "Başar Başaran",
                "first_name": "Başar",
                "honorific": "Bey",
                "role": "Co-Founder & CEO",
                "email": "basar@kunduz.com",
                "personalization": "Kunduz'un Y Combinator desteğiyle milyonlarca öğrenciye ulaşan eğitim teknolojisi vizyonu"
            },
            {
                "full_name": "Melih Şener",
                "first_name": "Melih",
                "honorific": "Bey",
                "role": "Co-Founder & CTO",
                "email": "melih@kunduz.com",
                "personalization": "Kunduz'un yapay zeka ve eğitmen ağını birleştiren yüksek etkileşimli mobil ürün mimarisi"
            }
        ]
    },
    {
        "name": "Yolda.com",
        "domain": "yolda.com",
        "sector": "Logistics / SaaS",
        "description": "B2B dijital lojistik ve taşımacılık yönetim SaaS platformu",
        "founders": [
            {"name": "Volkan Özkan", "title": "Co-Founder & CEO", "university": "Boğaziçi Üniv.", "prev": "McKinsey / Speedinvest"},
            {"name": "C. Murad Özsert", "title": "Co-Founder", "university": "Boğaziçi Üniv.", "prev": "Yolda.com"}
        ],
        "leads": [
            {
                "full_name": "Volkan Özkan",
                "first_name": "Volkan",
                "honorific": "Bey",
                "role": "Co-Founder & CEO",
                "email": "volkan@yolda.com",
                "personalization": "Yolda.com'un Speedinvest yatırımıyla Avrupa ve Türkiye'de B2B lojistiği dijitalleştiren yenilikçi platformu"
            },
            {
                "full_name": "C. Murad Özsert",
                "first_name": "Murad",
                "honorific": "Bey",
                "role": "Co-Founder",
                "email": "murad@yolda.com",
                "personalization": "Yolda.com'un tedarik zinciri operasyonlarında verimlilik ve şeffaflık sağlayan güçlü teknoloji altyapısı"
            }
        ]
    },
    {
        "name": "Loop Games",
        "domain": "loopgames.net",
        "sector": "Gaming",
        "description": "Match 3D ile küresel listelerde zirveye yerleşen mobil oyun stüdyosu",
        "founders": [
            {"name": "Mert Can", "title": "Founder & CEO", "university": "Bilkent Üniv.", "prev": "Global Hit Maker"}
        ],
        "leads": [
            {
                "full_name": "Mert Can",
                "first_name": "Mert",
                "honorific": "Bey",
                "role": "Founder & CEO",
                "email": "mert@loopgames.net",
                "is_gaming": True
            }
        ]
    },
    {
        "name": "Kolay İK",
        "domain": "kolayik.com",
        "sector": "HRTech / SaaS",
        "description": "Şirketler için bulut tabanlı insan kaynakları ve bordro yönetim SaaS platformu",
        "founders": [
            {"name": "Efecan Erdur", "title": "Co-Founder & CEO", "university": "Boğaziçi Üniv.", "prev": "VC backed"},
            {"name": "Çağlar Yalı", "title": "Co-Founder", "university": "Boğaziçi Üniv.", "prev": "Kolay İK"}
        ],
        "leads": [
            {
                "full_name": "Efecan Erdur",
                "first_name": "Efecan",
                "honorific": "Bey",
                "role": "Co-Founder & CEO",
                "email": "efecan@kolayik.com",
                "personalization": "Kolay İK'nın binlerce şirkette çalışan deneyimi ve İK süreçlerini sadeleştiren başarılı SaaS ekosistemi"
            },
            {
                "full_name": "Çağlar Yalı",
                "first_name": "Çağlar",
                "honorific": "Bey",
                "role": "Co-Founder",
                "email": "caglar@kolayik.com",
                "personalization": "Kolay İK'nın kullanıcı dostu arayüzü ve şirket içi operasyonları hızlandıran modüler yapısı"
            }
        ]
    },
    {
        "name": "Tarfin",
        "domain": "tarfin.com",
        "sector": "AgriTech / FinTech",
        "description": "Çiftçiler için tarımsal girdi finansmanı ve tedarik SaaS platformu",
        "founders": [
            {"name": "Mehmet Memecan", "title": "Founder & CEO", "university": "Wharton / Columbia", "prev": "Quona / Syngenta backed"}
        ],
        "leads": [
            {
                "full_name": "Mehmet Memecan",
                "first_name": "Mehmet",
                "honorific": "Bey",
                "role": "Founder & CEO",
                "email": "mehmet@tarfin.com",
                "personalization": "Tarfin'in veri ve makine öğrenimiyle tarımsal finansmana erişimi kolaylaştıran etki odaklı modeli"
            }
        ]
    },
    {
        "name": "Twin Science",
        "domain": "twinscience.com",
        "sector": "EdTech / AI & STEM",
        "description": "Çocuklar için sürdürülebilirlik ve yapay zeka odaklı STEM eğitim teknolojileri platformu",
        "founders": [
            {"name": "Asuhan Kartal", "title": "Co-Founder & CEO", "university": "Boğaziçi Üniv.", "prev": "YGA"},
            {"name": "Batuhan Apaydın", "title": "Co-Founder", "university": "Boğaziçi Üniv.", "prev": "YGA"}
        ],
        "leads": [
            {
                "full_name": "Asuhan Kartal",
                "first_name": "Asuhan",
                "honorific": "Hanım",
                "role": "Co-Founder & CEO",
                "email": "asuhan@twinscience.com",
                "personalization": "Twin Science'ın Birleşik Krallık ve global pazarda çocuklara yapay zeka ve sürdürülebilirlik bilinci aşılayan eğitim vizyonu"
            },
            {
                "full_name": "Batuhan Apaydın",
                "first_name": "Batuhan",
                "honorific": "Bey",
                "role": "Co-Founder",
                "email": "batuhan@twinscience.com",
                "personalization": "Twin Science'ın ödüllü STEM setleri ve dijital öğrenme platformuyla yakaladığı küresel başarı"
            }
        ]
    },
    {
        "name": "Glocalzone",
        "domain": "glocalzone.com",
        "sector": "P2P Marketplace / SaaS",
        "description": "Gezginler ve alıcıları buluşturan sınır ötesi P2P alışveriş platformu",
        "founders": [
            {"name": "Doğan Turan", "title": "Co-Founder & CEO", "university": "Boğaziçi Üniv.", "prev": "Glocalzone"},
            {"name": "Büşra Kaya", "title": "Co-Founder", "university": "Boğaziçi Üniv.", "prev": "Glocalzone"}
        ],
        "leads": [
            {
                "full_name": "Doğan Turan",
                "first_name": "Doğan",
                "honorific": "Bey",
                "role": "Co-Founder & CEO",
                "email": "dogan@glocalzone.com",
                "personalization": "Glocalzone'un sınır ötesi alışverişte yarattığı güvenli topluluk ve küresel pazar yeri dinamizmi"
            },
            {
                "full_name": "Büşra Kaya",
                "first_name": "Büşra",
                "honorific": "Hanım",
                "role": "Co-Founder",
                "email": "busra@glocalzone.com",
                "personalization": "Glocalzone'un seyahat edenler ile ürün talep edenleri eşleştiren yenilikçi ürün deneyimi"
            }
        ]
    },
    {
        "name": "Ekmob",
        "domain": "ekmob.com",
        "sector": "SaaS / Field Sales",
        "description": "Mobil saha satış ve ekip yönetim SaaS platformu",
        "founders": [
            {"name": "Sunay Şener", "title": "Founder & CEO", "university": "İTÜ", "prev": "StartersHub backed"}
        ],
        "leads": [
            {
                "full_name": "Sunay Şener",
                "first_name": "Sunay",
                "honorific": "Bey",
                "role": "Founder & CEO",
                "email": "sunay@ekmob.com",
                "personalization": "Ekmob'un kurumsal satış ekiplerinin saha verimliliğini ve rota optimizasyonunu artıran mobil SaaS çözümleri"
            }
        ]
    },
    {
        "name": "CarbonGate",
        "domain": "carbongate.io",
        "sector": "ClimateTech / ESG SaaS",
        "description": "Şirketler için karbon ayak izi hesaplama ve ESG raporlama SaaS platformu",
        "founders": [
            {"name": "Eren Can Kırmızı", "title": "Founder & CEO", "university": "İTÜ", "prev": "ClimateTech"}
        ],
        "leads": [
            {
                "full_name": "Eren Can Kırmızı",
                "first_name": "Eren Can",
                "honorific": "Bey",
                "role": "Founder & CEO",
                "email": "eren@carbongate.io",
                "personalization": "CarbonGate'in kurumsal karbon emisyonlarını ölçme ve sürdürülebilirlik raporlamasını otomatikleştiren platformu"
            }
        ]
    },
    {
        "name": "Octovan",
        "domain": "octovan.com",
        "sector": "Logistics / SaaS",
        "description": "Şehir içi lojistik, parça ve evden eve taşımacılık dijital platformu",
        "founders": [
            {"name": "Erhan Güneş", "title": "Co-Founder & CEO", "university": "Boğaziçi Üniv.", "prev": "Octovan"},
            {"name": "Sercan Dağdelen", "title": "Co-Founder", "university": "Boğaziçi Üniv.", "prev": "Octovan"}
        ],
        "leads": [
            {
                "full_name": "Erhan Güneş",
                "first_name": "Erhan",
                "honorific": "Bey",
                "role": "Co-Founder & CEO",
                "email": "erhan@octovan.com",
                "personalization": "Octovan'ın akıllı eşleştirme ve sabit fiyat garantisiyle taşımacılık sektörüne getirdiği standartlar"
            },
            {
                "full_name": "Sercan Dağdelen",
                "first_name": "Sercan",
                "honorific": "Bey",
                "role": "Co-Founder",
                "email": "sercan@octovan.com",
                "personalization": "Octovan'ın operasyonel süreçleri dijitalleştirerek müşteri memnuniyetini artıran lojistik altyapısı"
            }
        ]
    },
    {
        "name": "Qooper",
        "domain": "qooper.io",
        "sector": "HRTech / SaaS",
        "description": "Kurumsal mentörlük, koçluk ve çalışan gelişimi SaaS platformu",
        "founders": [
            {"name": "Ömer Kaya", "title": "Founder & CEO", "university": "Chicago / Techstars", "prev": "500 Istanbul backed"}
        ],
        "leads": [
            {
                "full_name": "Ömer Kaya",
                "first_name": "Ömer",
                "honorific": "Bey",
                "role": "Founder & CEO",
                "email": "omer@qooper.io",
                "personalization": "Qooper'ın Fortune 500 şirketlerinde çalışan bağlılığı ve mentörlük programlarını ölçekleyen global SaaS başarısı"
            }
        ]
    },
    {
        "name": "Norma",
        "domain": "norma.co",
        "sector": "FinTech / SaaS",
        "description": "Serbest çalışanlar ve KOBİ'ler için finansal yönetim ve faturalama platformu",
        "founders": [
            {"name": "Hakan Ertürk", "title": "Co-Founder & CEO", "university": "Boğaziçi Üniv.", "prev": "FinTech Veteran"},
            {"name": "Murat Erdönmez", "title": "Co-Founder", "university": "Tech Entrepreneur", "prev": "Norma"}
        ],
        "leads": [
            {
                "full_name": "Hakan Ertürk",
                "first_name": "Hakan",
                "honorific": "Bey",
                "role": "Co-Founder & CEO",
                "email": "hakan@norma.co",
                "personalization": "Norma'nın KOBİ ve serbest çalışanların tüm finans ve ön muhasebe süreçlerini tek panelde toplayan yenilikçi çözümü"
            },
            {
                "full_name": "Murat Erdönmez",
                "first_name": "Murat",
                "honorific": "Bey",
                "role": "Co-Founder",
                "email": "murat@norma.co",
                "personalization": "Norma'nın kullanıcı dostu dijital bankacılık ve finansal asistanlık araçlarıyla sağladığı kolaylıklar"
            }
        ]
    },
    {
        "name": "Paket Mutfak",
        "domain": "paketmutfak.com.tr",
        "sector": "FoodTech / Cloud Kitchen",
        "description": "Restoranlar için bulut mutfak ve sipariş operasyon altyapısı",
        "founders": [
            {"name": "Tali Gürbüz", "title": "Founder & CEO", "university": "Boğaziçi Üniv.", "prev": "McKinsey"}
        ],
        "leads": [
            {
                "full_name": "Tali Gürbüz",
                "first_name": "Tali",
                "honorific": "Bey",
                "role": "Founder & CEO",
                "email": "tali@paketmutfak.com.tr",
                "personalization": "Paket Mutfak'ın veri odaklı lokasyon seçimi ve çok markalı bulut mutfak modeliyle gıda sektörüne getirdiği verimlilik"
            }
        ]
    },
    {
        "name": "ServisSoft",
        "domain": "servissoft.net",
        "sector": "SaaS / Field Service",
        "description": "Satış sonrası hizmetler ve teknik servis yönetim SaaS platformu",
        "founders": [
            {"name": "Canberk Mersin", "title": "Founder & CEO", "university": "İTÜ", "prev": "ServisSoft"}
        ],
        "leads": [
            {
                "full_name": "Canberk Mersin",
                "first_name": "Canberk",
                "honorific": "Bey",
                "role": "Founder & CEO",
                "email": "canberk@servissoft.net",
                "personalization": "ServisSoft'un teknik servis ve garanti takip süreçlerini dijitalleştirerek müşteri sadakatini artıran SaaS platformu"
            }
        ]
    },
    {
        "name": "Invio",
        "domain": "invio.tech",
        "sector": "FinTech / SaaS",
        "description": "Finansal kurumlar için açık bankacılık ve dijital dönüşüm çözümleri",
        "founders": [
            {"name": "Çağdaş Güven", "title": "Founder & CEO", "university": "İTÜ", "prev": "Invio"}
        ],
        "leads": [
            {
                "full_name": "Çağdaş Güven",
                "first_name": "Çağdaş",
                "honorific": "Bey",
                "role": "Founder & CEO",
                "email": "cagdas@invio.tech",
                "personalization": "Invio'nun açık bankacılık ve fintech entegrasyonlarında sunduğu yüksek güvenlikli ve ölçeklenebilir altyapı"
            }
        ]
    },
    {
        "name": "Virasoft",
        "domain": "virasoft.com.tr",
        "sector": "HealthTech / AI",
        "description": "Dijital patoloji ve yapay zeka destekli kanser teşhis platformu",
        "founders": [
            {"name": "Gökhan Polat", "title": "Founder & CEO", "university": "ODTÜ", "prev": "StartersHub backed"}
        ],
        "leads": [
            {
                "full_name": "Gökhan Polat",
                "first_name": "Gokhan",
                "honorific": "Bey",
                "role": "Founder & CEO",
                "email": "gokhan@virasoft.com.tr",
                "personalization": "Virasoft'un dijital patolojide yapay zeka algoritmalarıyla teşhis doğruluğunu ve hızını artıran çığır açıcı çalışmaları"
            }
        ]
    },
    {
        "name": "Bigger Games",
        "domain": "biggergames.com",
        "sector": "Gaming",
        "description": "Casual ve puzzle türünde milyonlarca oyuncuya ulaşan mobil oyun stüdyosu",
        "founders": [
            {"name": "Hakan Ulvan", "title": "Co-Founder & CEO", "university": "Boğaziçi Üniv.", "prev": "Peak Games / Index Ventures"},
            {"name": "Erkan Gözütok", "title": "Co-Founder", "university": "Boğaziçi Üniv.", "prev": "Bigger Games"}
        ],
        "leads": [
            {
                "full_name": "Hakan Ulvan",
                "first_name": "Hakan",
                "honorific": "Bey",
                "role": "Co-Founder & CEO",
                "email": "hakan@biggergames.com",
                "is_gaming": True
            },
            {
                "full_name": "Erkan Gözütok",
                "first_name": "Erkan",
                "honorific": "Bey",
                "role": "Co-Founder",
                "email": "erkan@biggergames.com",
                "is_gaming": True
            }
        ]
    },
    {
        "name": "Panteon",
        "domain": "panteon.games",
        "sector": "Gaming",
        "description": "Türkiye'nin köklü mobil oyun stüdyolarından biri (ODTÜ Teknokent)",
        "founders": [
            {"name": "Ufuk Şahin", "title": "Founder & CEO", "university": "ODTÜ", "prev": "Panteon"}
        ],
        "leads": [
            {
                "full_name": "Ufuk Şahin",
                "first_name": "Ufuk",
                "honorific": "Bey",
                "role": "Founder & CEO",
                "email": "ufuk@panteon.games",
                "is_gaming": True
            }
        ]
    }
]


def render_general(first_name: str, honorific: str, company_name: str, personalization: str) -> tuple[str, str]:
    template = Path("templates/email_tr.txt").read_text(encoding="utf-8")
    lines = template.strip().split("\n")
    subject = lines[0].replace("SUBJECT:", "").strip()
    body = "\n".join(lines[1:]).strip()
    body = body.replace("{{first_name}}", first_name)
    body = body.replace("{{honorific}}", honorific)
    body = body.replace("{{company_name}}", company_name)
    body = body.replace("{{personalization_paragraph}}", personalization)
    # Ensure no # comments remain
    body = body.split("#")[0].strip()
    return subject, body


def render_gaming(first_name: str, honorific: str, company_name: str) -> tuple[str, str]:
    template = Path("templates/email_gaming_tr.txt").read_text(encoding="utf-8")
    lines = template.strip().split("\n")
    subject = lines[0].replace("SUBJECT:", "").strip()
    body = "\n".join(lines[1:]).strip()
    body = body.replace("{{first_name}}", first_name)
    body = body.replace("{{honorific}}", honorific)
    body = body.replace("{{company_name}}", company_name)
    body = body.split("#")[0].strip()
    return subject, body


def main():
    conn = db.get_connection()
    c = conn.cursor()

    camp_name = "Wave 8 — 20 Tech & Gaming Startups"
    c.execute("""
        INSERT INTO campaigns (name, target_leads, approved, status)
        VALUES (?, ?, 1, 'SENDING')
    """, (camp_name, 0))
    campaign_id = c.lastrowid

    inserted_lead_ids = []

    for comp in WAVE8_COMPANIES:
        c.execute("""
            INSERT INTO companies (name, website, domain, sector, description, classification, researched_at)
            VALUES (?, ?, ?, ?, ?, 'OUTREACH', datetime('now'))
        """, (comp["name"], f"https://{comp['domain']}", comp["domain"], comp["sector"], comp["description"]))
        company_id = c.lastrowid

        for f in comp.get("founders", []):
            c.execute("""
                INSERT INTO founders (company_id, full_name, title, university, previous_companies)
                VALUES (?, ?, ?, ?, ?)
            """, (company_id, f["name"], f["title"], f.get("university"), f.get("prev")))

        for lead in comp.get("leads", []):
            if lead.get("is_gaming"):
                subject, body = render_gaming(lead["first_name"], lead["honorific"], comp["name"])
            else:
                subject, body = render_general(lead["first_name"], lead["honorific"], comp["name"], lead["personalization"])

            c.execute("""
                INSERT INTO leads (
                    company_id, full_name, first_name, title, honorific,
                    email, email_verification_status, status, subject, rendered_body, attachment_path, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, 'VERIFIED', 'APPROVED', ?, ?, 'assets/erdogan_kocabas_cv.pdf', datetime('now'), datetime('now'))
            """, (
                company_id, lead["full_name"], lead["first_name"], lead["role"], lead["honorific"],
                lead["email"], subject, body
            ))
            inserted_lead_ids.append(c.lastrowid)

    c.execute("UPDATE campaigns SET target_leads = ? WHERE id = ?", (len(inserted_lead_ids), campaign_id))
    conn.commit()

    logger.info("Ingested %d companies, %d leads. Starting dispatch with 30s pacing...", len(WAVE8_COMPANIES), len(inserted_lead_ids))

    cv_path = Path("assets/erdogan_kocabas_cv.pdf")
    if not cv_path.exists():
        logger.error("CV not found at %s", cv_path)
        sys.exit(1)

    sender_email = os.getenv("GMAIL_SENDER_EMAIL", "").strip()
    app_pwd = os.getenv("GMAIL_APP_PASSWORD", "").strip()

    if not sender_email or not app_pwd:
        logger.error("GMAIL credentials missing in .env")
        sys.exit(1)

    istanbul_tz = ZoneInfo("Europe/Istanbul")
    sent_count = 0
    fail_count = 0

    print("=" * 60)
    print(f"DISPATCHING WAVE 8 ({len(inserted_lead_ids)} leads, 30s interval)")
    print(f"Sender: {sender_email}")
    print("=" * 60)

    for i, lead_id in enumerate(inserted_lead_ids):
        lead_row = conn.execute("""
            SELECT l.id, l.full_name, l.first_name, l.email, l.subject, l.rendered_body, c.name as company_name
            FROM leads l JOIN companies c ON l.company_id = c.id
            WHERE l.id = ?
        """, (lead_id,)).fetchone()
        lead = dict(lead_row)

        send_id = db.create_send(conn, {
            "campaign_id": campaign_id,
            "lead_id": lead["id"],
            "scheduled_at": datetime.now(istanbul_tz).isoformat(),
        })

        try:
            db.update_send(conn, send_id, {
                "attempted_at": datetime.now(istanbul_tz).isoformat(),
            })

            logger.info("[%d/%d] Sending to %s <%s> @ %s...", i + 1, len(inserted_lead_ids), lead['full_name'], lead['email'], lead['company_name'])

            msg_id = smtp_client.send_smtp_email(
                to=lead["email"],
                subject=lead["subject"],
                body=lead["rendered_body"],
                attachment_path="assets/erdogan_kocabas_cv.pdf",
                sender_email=sender_email,
                app_password=app_pwd,
            )

            db.update_send(conn, send_id, {
                "sent_at": datetime.now(istanbul_tz).isoformat(),
                "gmail_message_id": msg_id,
            })

            conn.execute("UPDATE leads SET status = 'SENT' WHERE id = ?", (lead["id"],))
            conn.commit()
            sent_count += 1
            logger.info("  ✓ SUCCESS — Message ID: %s", msg_id)

        except Exception as e:
            fail_count += 1
            logger.error("  ✗ FAILED to send to %s: %s", lead['email'], e)
            db.update_send(conn, send_id, {
                "error_code": type(e).__name__,
                "error_message": str(e)[:500],
            })
            conn.execute("UPDATE leads SET status = 'FAILED' WHERE id = ?", (lead["id"],))
            conn.commit()

        if i < len(inserted_lead_ids) - 1:
            logger.info("  ... Pacing 30 seconds before next send ...")
            time.sleep(30)

    conn.execute("UPDATE campaigns SET status = 'COMPLETED' WHERE id = ?", (campaign_id,))
    conn.commit()
    export()

    print("=" * 60)
    print(f"WAVE 8 COMPLETED: {sent_count} sent, {fail_count} failed")
    print("=" * 60)
    conn.close()


if __name__ == "__main__":
    main()
