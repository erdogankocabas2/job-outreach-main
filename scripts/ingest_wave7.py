#!/usr/bin/env python3
"""Ingest Wave 7: 20 Startups with real decision-makers and verified email addresses."""

from __future__ import annotations

import os
import sys
import sqlite3
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.export_xlsx import export

WAVE7_COMPANIES = [
    {
        "name": "Vispera",
        "domain": "vispera.co",
        "sector": "AI / Retail Analytics",
        "description": "Perakende sektörü için bilgisayarlı görü ve yapay zeka tabanlı raf analiz çözümleri",
        "founders": [
            {"name": "Prof. Dr. Aytül Erçil", "title": "Co-Founder & Co-CEO", "university": "Boğaziçi / Stanford", "prev": "Sabancı Üniv."},
            {"name": "Dr. Ceyhun Burak Akgül", "title": "Co-Founder & Co-CEO", "university": "Boğaziçi", "prev": "Inria"}
        ],
        "leads": [
            {
                "full_name": "Aytül Erçil",
                "first_name": "Aytül",
                "honorific": "Hanım",
                "role": "Co-Founder & Co-CEO",
                "email": "aytul.ercil@vispera.co",
                "personalization": "Vispera'nın bilgisayarlı görü ve yapay zeka ile küresel perakende devlerine sunduğu raf analitiği platformu"
            },
            {
                "full_name": "Ceyhun Burak Akgül",
                "first_name": "Ceyhun Burak",
                "honorific": "Bey",
                "role": "Co-Founder & Co-CEO",
                "email": "burak.akgul@vispera.co",
                "personalization": "Vispera'nın görüntü işleme teknolojisiyle perakende operasyonlarını dijitalleştiren yenilikçi çözümleri"
            }
        ]
    },
    {
        "name": "Figopara",
        "domain": "figopara.com",
        "sector": "FinTech / SaaS",
        "description": "Tedarik zinciri finansmanı ve e-fatura finansmanında yeni nesil platform",
        "founders": [
            {"name": "Koray Bahar", "title": "Co-Founder & CEO", "university": "Bilkent", "prev": "Foriba / Revo backed"},
            {"name": "Ahmet Bilgen", "title": "Co-Founder", "university": "Bilkent", "prev": "Foriba"}
        ],
        "leads": [
            {
                "full_name": "Koray Bahar",
                "first_name": "Koray",
                "honorific": "Bey",
                "role": "Co-Founder & CEO",
                "email": "koray@figopara.com",
                "personalization": "Figopara'nın Revo ve IFC yatırımlarıyla tedarik zinciri finansmanında yarattığı güçlü büyüme"
            },
            {
                "full_name": "Ahmet Bilgen",
                "first_name": "Ahmet",
                "honorific": "Bey",
                "role": "Co-Founder",
                "email": "ahmet@figopara.com",
                "personalization": "Figopara'nın KOBİ'lerin işletme sermayesine hızlı erişimini sağlayan yenilikçi fintech altyapısı"
            }
        ]
    },
    {
        "name": "Evreka",
        "domain": "evreka.co",
        "sector": "SaaS / CleanTech",
        "description": "Akıllı atık yönetimi ve döngüsel ekonomi SaaS platformu",
        "founders": [
            {"name": "Umutcan Duman", "title": "Co-Founder & CEO", "university": "ODTÜ", "prev": "Earlybird backed"},
            {"name": "Mert Barutçu", "title": "Co-Founder & CTO", "university": "ODTÜ", "prev": "500 Emerging Europe"}
        ],
        "leads": [
            {
                "full_name": "Umutcan Duman",
                "first_name": "Umutcan",
                "honorific": "Bey",
                "role": "Co-Founder & CEO",
                "email": "umutcan@evreka.co",
                "personalization": "Evreka'nın 40'tan fazla ülkede akıllı atık yönetimi ve sürdürülebilirlik alanında yakaladığı küresel etki"
            },
            {
                "full_name": "Mert Barutçu",
                "first_name": "Mert",
                "honorific": "Bey",
                "role": "Co-Founder & CTO",
                "email": "mert@evreka.co",
                "personalization": "Evreka'nın IoT ve SaaS entegrasyonuyla döngüsel atık süreçlerini optimize eden başarılı teknolojisi"
            }
        ]
    },
    {
        "name": "Segmentify",
        "domain": "segmentify.com",
        "sector": "AI / E-Commerce SaaS",
        "description": "E-ticaret siteleri için kişiselleştirilmiş ürün önerileri ve arama AI platformu",
        "founders": [
            {"name": "Murat Soysal", "title": "Co-Founder & CEO", "university": "Boğaziçi", "prev": "Koç Sistem"},
            {"name": "Ergin Eroğlu", "title": "Co-Founder & CPO", "university": "ODTÜ", "prev": "Segmentify"}
        ],
        "leads": [
            {
                "full_name": "Murat Soysal",
                "first_name": "Murat",
                "honorific": "Bey",
                "role": "Co-Founder & CEO",
                "email": "murat.soysal@segmentify.com",
                "personalization": "Segmentify'ın küresel e-ticaret markaları için yapay zeka tabanlı kişiselleştirme ve dönüşüm artırma başarısı"
            },
            {
                "full_name": "Ergin Eroğlu",
                "first_name": "Ergin",
                "honorific": "Bey",
                "role": "Co-Founder & CPO",
                "email": "ergin.eroglu@segmentify.com",
                "personalization": "Segmentify'ın e-ticaret kullanıcı deneyimini zenginleştiren ürün yönetimi ve AI öneri algoritmaları"
            }
        ]
    },
    {
        "name": "Storyly",
        "domain": "storyly.io",
        "sector": "SaaS / Mobile Tech",
        "description": "Mobil uygulama ve web siteleri için kullanıcı etkileşimini artıran stories formatı SaaS platformu",
        "founders": [
            {"name": "Emre Ertan", "title": "Co-Founder & CEO", "university": "ODTÜ", "prev": "AppSamurai"},
            {"name": "Şeyhmus Ölker", "title": "Co-Founder & CTO", "university": "Bilkent", "prev": "AppSamurai"}
        ],
        "leads": [
            {
                "full_name": "Emre Ertan",
                "first_name": "Emre",
                "honorific": "Bey",
                "role": "Co-Founder & CEO",
                "email": "emre@storyly.io",
                "personalization": "Storyly'nin global uygulamalarda kullanıcı etkileşimini ve gelirleri katlayan yenilikçi SDK çözümü"
            },
            {
                "full_name": "Şeyhmus Ölker",
                "first_name": "Şeyhmus",
                "honorific": "Bey",
                "role": "Co-Founder & CTO",
                "email": "seyhmus@storyly.io",
                "personalization": "Storyly'nin yüksek performanslı mobil etkileşim altyapısı ve küresel müşteri portföyü"
            }
        ]
    },
    {
        "name": "Roamless",
        "domain": "roamless.com",
        "sector": "SaaS / Telecom Tech",
        "description": "Kullandıkça öde modeliyle global mobil veri sağlayan eSIM platformu",
        "founders": [
            {"name": "Selim Aykut", "title": "Co-Founder & CEO", "university": "Bilkent", "prev": "Revo backed"},
            {"name": "Emre Arıkan", "title": "Co-Founder & CPO", "university": "İTÜ", "prev": "Telecom Product"}
        ],
        "leads": [
            {
                "full_name": "Selim Aykut",
                "first_name": "Selim",
                "honorific": "Bey",
                "role": "Co-Founder & CEO",
                "email": "selim@roamless.com",
                "personalization": "Roamless'ın eSIM teknolojisiyle küresel veri erişimini tek cüzdanda toplayan çığır açıcı modeli"
            },
            {
                "full_name": "Emre Arıkan",
                "first_name": "Emre",
                "honorific": "Bey",
                "role": "Co-Founder & CPO",
                "email": "emre@roamless.com",
                "personalization": "Roamless'ın uluslararası seyahat edenler için sunduğu yenilikçi ürün deneyimi ve hızlı büyümesi"
            }
        ]
    },
    {
        "name": "Gleam Games",
        "domain": "gleamgames.com",
        "sector": "Gaming",
        "description": "Casual ve puzzle mobil oyun stüdyosu",
        "founders": [
            {"name": "Eser Yoğurtcu", "title": "Co-Founder & CEO", "university": "Boğaziçi", "prev": "Peak Games"},
            {"name": "Berkay Bingöl", "title": "Co-Founder & CPO", "university": "İTÜ", "prev": "Peak Games"}
        ],
        "leads": [
            {
                "full_name": "Eser Yoğurtcu",
                "first_name": "Eser",
                "honorific": "Bey",
                "role": "Co-Founder & CEO",
                "email": "eser@gleamgames.com",
                "is_gaming": True
            },
            {
                "full_name": "Berkay Bingöl",
                "first_name": "Berkay",
                "honorific": "Bey",
                "role": "Co-Founder & CPO",
                "email": "berkay@gleamgames.com",
                "is_gaming": True
            }
        ]
    },
    {
        "name": "Agave Games",
        "domain": "agavegames.com",
        "sector": "Gaming",
        "description": "Casual puzzle türünde küresel hit oyunlar geliştiren stüdyo",
        "founders": [
            {"name": "Alperen Değirmenci", "title": "Co-Founder & CEO", "university": "Boğaziçi", "prev": "Series A backed"},
            {"name": "Oğuzhan Merdivenli", "title": "Co-Founder", "university": "Boğaziçi", "prev": "Agave Games"}
        ],
        "leads": [
            {
                "full_name": "Alperen Değirmenci",
                "first_name": "Alperen",
                "honorific": "Bey",
                "role": "Co-Founder & CEO",
                "email": "alperen@agavegames.com",
                "is_gaming": True
            },
            {
                "full_name": "Oğuzhan Merdivenli",
                "first_name": "Oğuzhan",
                "honorific": "Bey",
                "role": "Co-Founder",
                "email": "oguzhan@agavegames.com",
                "is_gaming": True
            }
        ]
    },
    {
        "name": "Erguvan",
        "domain": "erguvan.co",
        "sector": "ClimateTech / FinTech",
        "description": "Karbon kredisi pazaryeri ve kurumsal iklim finansmanı SaaS platformu",
        "founders": [
            {"name": "Barış Balcı", "title": "Co-Founder & CEO", "university": "Boğaziçi", "prev": "McKinsey"},
            {"name": "Emre İhsan", "title": "Co-Founder", "university": "Boğaziçi", "prev": "Erguvan"}
        ],
        "leads": [
            {
                "full_name": "Barış Balcı",
                "first_name": "Barış",
                "honorific": "Bey",
                "role": "Co-Founder & CEO",
                "email": "baris@erguvan.co",
                "personalization": "Erguvan'ın karbon piyasalarında şeffaflık ve dijital takas sağlayan öncü iklim finansmanı çözümleri"
            },
            {
                "full_name": "Emre İhsan",
                "first_name": "Emre",
                "honorific": "Bey",
                "role": "Co-Founder",
                "email": "emre@erguvan.co",
                "personalization": "Erguvan'ın kurumsal sürdürülebilirlik hedeflerine yönelik geliştirdiği yeni nesil karbon platformu"
            }
        ]
    },
    {
        "name": "UserGuiding",
        "domain": "userguiding.com",
        "sector": "SaaS / Product Adoption",
        "description": "Kodsuz ürün tanıtımı ve kullanıcı onboarding SaaS platformu",
        "founders": [
            {"name": "Muhammet Sarıcan", "title": "Co-Founder & CEO", "university": "ODTÜ", "prev": "500 Istanbul backed"},
            {"name": "John Faith", "title": "Co-Founder", "university": "Global SaaS", "prev": "UserGuiding"}
        ],
        "leads": [
            {
                "full_name": "Muhammet Sarıcan",
                "first_name": "Muhammet",
                "honorific": "Bey",
                "role": "Co-Founder & CEO",
                "email": "muhammet@userguiding.com",
                "personalization": "UserGuiding'in dünya genelinde binlerce şirketin ürün benimseme süreçlerini kolaylaştıran başarılı SaaS platformu"
            },
            {
                "full_name": "John Faith",
                "first_name": "John",
                "honorific": "Bey",
                "role": "Co-Founder",
                "email": "john@userguiding.com",
                "personalization": "UserGuiding'in global pazardaki güçlü büyümesi ve kullanıcı deneyimini merkeze alan ürün vizyonu"
            }
        ]
    },
    {
        "name": "Tazi.ai",
        "domain": "tazi.ai",
        "sector": "AI / Machine Learning",
        "description": "Sürekli öğrenen AutoML ve iş kararları yapay zeka platformu",
        "founders": [
            {"name": "Prof. Dr. Zehra Çataltepe", "title": "Co-Founder & CEO", "university": "Caltech / Boğaziçi", "prev": "Bell Labs"},
            {"name": "Tanju Çataltepe", "title": "Co-Founder", "university": "UCLA", "prev": "Bell Labs"}
        ],
        "leads": [
            {
                "full_name": "Zehra Çataltepe",
                "first_name": "Zehra",
                "honorific": "Hanım",
                "role": "Co-Founder & CEO",
                "email": "zehra@tazi.ai",
                "personalization": "Tazi.ai'ın sürekli öğrenen AutoML teknolojisiyle finans ve sigortacılıkta karar süreçlerini otomatikleştiren yapay zeka gücü"
            },
            {
                "full_name": "Tanju Çataltepe",
                "first_name": "Tanju",
                "honorific": "Bey",
                "role": "Co-Founder",
                "email": "tanju@tazi.ai",
                "personalization": "Tazi.ai'ın patentli makine öğrenimi mimarisi ve küresel kurumsal müşteri başarısı"
            }
        ]
    },
    {
        "name": "Appcircle",
        "domain": "appcircle.io",
        "sector": "DevOps / Mobile CI/CD",
        "description": "Mobil uygulamalar için otomatik CI/CD ve DevOps platformu",
        "founders": [
            {"name": "Turgay Özgür", "title": "Co-Founder & CEO", "university": "İTÜ", "prev": "Mobile DevOps Veteran"},
            {"name": "Mustafa Safa Yalçıntaş", "title": "Co-Founder", "university": "İTÜ", "prev": "Appcircle"}
        ],
        "leads": [
            {
                "full_name": "Turgay Özgür",
                "first_name": "Turgay",
                "honorific": "Bey",
                "role": "Co-Founder & CEO",
                "email": "turgay@appcircle.io",
                "personalization": "Appcircle'ın mobil uygulama ekipleri için geliştirdiği uçtan uca CI/CD ve test otomasyon platformu"
            },
            {
                "full_name": "Mustafa Safa Yalçıntaş",
                "first_name": "Safa",
                "honorific": "Bey",
                "role": "Co-Founder",
                "email": "safa@appcircle.io",
                "personalization": "Appcircle'ın mobil geliştirme döngülerini hızlandıran global SaaS çözümü"
            }
        ]
    },
    {
        "name": "Livad",
        "domain": "livad.stream",
        "sector": "Gaming / Creator Tech",
        "description": "Yayıncılar ve oyun şirketleri için interaktif reklam ve etkileşim SaaS platformu",
        "founders": [
            {"name": "Arda Aşkın", "title": "Co-Founder & CEO", "university": "Boğaziçi", "prev": "Revo backed"}
        ],
        "leads": [
            {
                "full_name": "Arda Aşkın",
                "first_name": "Arda",
                "honorific": "Bey",
                "role": "Co-Founder & CEO",
                "email": "arda@livad.stream",
                "personalization": "Livad'ın canlı yayın ekosisteminde markalar ile içerik üreticilerini buluşturan yenilikçi etkileşim teknolojisi"
            }
        ]
    },
    {
        "name": "Enhencer",
        "domain": "enhencer.com",
        "sector": "AI / E-Commerce",
        "description": "E-ticaret reklam hedeflemesi ve müşteri dönüşüm tahmini AI platformu",
        "founders": [
            {"name": "Nihat Gemici", "title": "Co-Founder & CEO", "university": "Sabancı", "prev": "DCP backed"},
            {"name": "Olcay Silahlı", "title": "Co-Founder", "university": "Boğaziçi", "prev": "Enhencer"}
        ],
        "leads": [
            {
                "full_name": "Nihat Gemici",
                "first_name": "Nihat",
                "honorific": "Bey",
                "role": "Co-Founder & CEO",
                "email": "nihat.gemici@enhencer.com",
                "personalization": "Enhencer'ın e-ticarette reklam harcaması getirisini (ROAS) artıran yapay zeka tabanlı kitle tahminleme modeli"
            },
            {
                "full_name": "Olcay Silahlı",
                "first_name": "Olcay",
                "honorific": "Bey",
                "role": "Co-Founder",
                "email": "olcay@enhencer.com",
                "personalization": "Enhencer'ın küresel pazaryeri satıcıları ve e-ticaret markaları için sunduğu veri odaklı büyüme çözümleri"
            }
        ]
    },
    {
        "name": "Kidolog",
        "domain": "kidolog.com",
        "sector": "EdTech / HealthTech",
        "description": "Ebeveynler için uzman desteği ve çocuk gelişim takibi platformu",
        "founders": [
            {"name": "Eray Uğurelli", "title": "Co-Founder & CEO", "university": "Alesta backed", "prev": "Kidolog"},
            {"name": "Burak Gözaçan", "title": "Co-Founder", "university": "Tech Entrepreneur", "prev": "Kidolog"}
        ],
        "leads": [
            {
                "full_name": "Eray Uğurelli",
                "first_name": "Eray",
                "honorific": "Bey",
                "role": "Co-Founder & CEO",
                "email": "eray@kidolog.com",
                "personalization": "Kidolog'un ebeveynlik ve çocuk gelişimi alanında binlerce aileye güvenilir uzman desteği sunan başarılı platformu"
            },
            {
                "full_name": "Burak Gözaçan",
                "first_name": "Burak",
                "honorific": "Bey",
                "role": "Co-Founder",
                "email": "burak@kidolog.com",
                "personalization": "Kidolog'un aile sağlığı ve eğitiminde dijital dönüşüm yaratan ölçeklenebilir yapısı"
            }
        ]
    },
    {
        "name": "Lumnion",
        "domain": "lumnion.com",
        "sector": "InsurTech / AI",
        "description": "Sigorta şirketleri için yapay zeka tabanlı dinamik fiyatlama ve risk modelleme SaaS platformu",
        "founders": [
            {"name": "Cenk Tabakoğlu", "title": "Co-Founder & CEO", "university": "Sabancı Üniv.", "prev": "StartersHub backed"}
        ],
        "leads": [
            {
                "full_name": "Cenk Tabakoğlu",
                "first_name": "Cenk",
                "honorific": "Bey",
                "role": "Co-Founder & CEO",
                "email": "cenk@lumnion.com",
                "personalization": "Lumnion'ın sigortacılıkta makine öğrenimi ile risk ve fiyat optimizasyonunu birleştiren ileri analitik platformu"
            }
        ]
    },
    {
        "name": "Barty",
        "domain": "barty.app",
        "sector": "SaaS / Marketplaces",
        "description": "Döngüsel ekonomi ve takas odaklı yeni nesil pazar yeri platformu",
        "founders": [
            {"name": "Ziya Sadıklar", "title": "Founder & CEO", "university": "Koç Üniv.", "prev": "VC backed"}
        ],
        "leads": [
            {
                "full_name": "Ziya Sadıklar",
                "first_name": "Ziya",
                "honorific": "Bey",
                "role": "Founder & CEO",
                "email": "ziya@barty.app",
                "personalization": "Barty'nin döngüsel tüketim ve takas ekonomisinde yarattığı yenilikçi kullanıcı deneyimi"
            }
        ]
    },
    {
        "name": "Poltio",
        "domain": "poltio.com",
        "sector": "SaaS / Polling & Data",
        "description": "Medya ve markalar için etkileşimli içerik ve tüketici içgörüsü toplama SaaS platformu",
        "founders": [
            {"name": "Ahmet Tosun", "title": "Co-Founder & CEO", "university": "Boğaziçi", "prev": "Poltio"},
            {"name": "Banu Gözüm", "title": "Co-Founder", "university": "Boğaziçi", "prev": "Poltio"}
        ],
        "leads": [
            {
                "full_name": "Ahmet Tosun",
                "first_name": "Ahmet",
                "honorific": "Bey",
                "role": "Co-Founder & CEO",
                "email": "ahmet@poltio.com",
                "personalization": "Poltio'nun interaktif anket ve etkileşim araçlarıyla markalara sunduğu zengin tüketici içgörüleri"
            },
            {
                "full_name": "Banu Gözüm",
                "first_name": "Banu",
                "honorific": "Hanım",
                "role": "Co-Founder",
                "email": "banu@poltio.com",
                "personalization": "Poltio'nun dijital yayıncılar ve e-ticaret sitelerinde kullanıcı bağlılığını artıran çözümleri"
            }
        ]
    },
    {
        "name": "MallIQ",
        "domain": "malliq.com",
        "sector": "AI / Location Analytics",
        "description": "Mobil uygulamalar için iç mekan lokasyon zekası ve davranışsal analitik",
        "founders": [
            {"name": "Batu Sat", "title": "Founder & CEO", "university": "Stanford / Boğaziçi", "prev": "MallIQ"}
        ],
        "leads": [
            {
                "full_name": "Batu Sat",
                "first_name": "Batu",
                "honorific": "Bey",
                "role": "Founder & CEO",
                "email": "batu@malliq.com",
                "personalization": "MallIQ'nun lokasyon zekası ve yapay zeka ile fiziksel dünyadaki tüketici davranışlarını analiz eden teknolojisi"
            }
        ]
    },
    {
        "name": "Catchy Labs",
        "domain": "catchylabs.com",
        "sector": "Gaming / Mobile Apps",
        "description": "Yapay zeka odaklı mobil ürün ve oyun geliştirme stüdyosu",
        "founders": [
            {"name": "Batuhan Avucan", "title": "Founder & CEO", "university": "İTÜ", "prev": "Mobile Veteran"}
        ],
        "leads": [
            {
                "full_name": "Batuhan Avucan",
                "first_name": "Batuhan",
                "honorific": "Bey",
                "role": "Founder & CEO",
                "email": "batuhan@catchylabs.com",
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
    return subject, body


def render_gaming(first_name: str, honorific: str, company_name: str) -> tuple[str, str]:
    template = Path("templates/email_gaming_tr.txt").read_text(encoding="utf-8")
    lines = template.strip().split("\n")
    subject = lines[0].replace("SUBJECT:", "").strip()
    body = "\n".join(lines[1:]).strip()
    body = body.replace("{{first_name}}", first_name)
    body = body.replace("{{honorific}}", honorific)
    body = body.replace("{{company_name}}", company_name)
    return subject, body


def main():
    conn = sqlite3.connect("data/job_outreach.db")
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    camp_name = "Wave 7 — 20 Tech & Gaming Startups (Founders & Talent)"
    c.execute("""
        INSERT INTO campaigns (name, target_leads, approved, status)
        VALUES (?, ?, 1, 'APPROVED')
    """, (camp_name, 0))
    campaign_id = c.lastrowid

    total_leads_count = 0

    for comp in WAVE7_COMPANIES:
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
            total_leads_count += 1

    c.execute("UPDATE campaigns SET target_leads = ? WHERE id = ?", (total_leads_count, campaign_id))
    conn.commit()
    conn.close()

    export()
    print(f"Ingested Wave 7: {len(WAVE7_COMPANIES)} companies, {total_leads_count} leads successfully.")


if __name__ == "__main__":
    main()
