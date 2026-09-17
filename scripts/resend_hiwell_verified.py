#!/usr/bin/env python3
"""Send verified Hiwell tailored application emails to Ozan Özçiçek, careers@hiwellapp.com, and hello@hiwellapp.com."""

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
logger = logging.getLogger("hiwell_verified")

RECIPIENTS = [
    {
        "name": "Ali Ozan Özçiçek",
        "salutation": "Ali Ozan Bey",
        "email": "ozan@hiwellapp.com",
        "role": "Founder & CEO"
    },
    {
        "name": "Ali Ozan Özçiçek (Kurumsal)",
        "salutation": "Ali Ozan Bey",
        "email": "ali.ozan@hiwellapp.com",
        "role": "Founder & CEO"
    },
    {
        "name": "Hiwell Yetenek & İşe Alım Ekibi",
        "salutation": "Hiwell Ekibi",
        "email": "careers@hiwellapp.com",
        "role": "Careers / Talent"
    },
    {
        "name": "Hiwell Ekibi",
        "salutation": "Hiwell Ekibi",
        "email": "hello@hiwellapp.com",
        "role": "General & Team"
    }
]

def build_body(salutation: str) -> str:
    return (
        f"Merhaba {salutation},\n\n"
        "Ben Erdoğan. Boğaziçi Üniversitesi endüstri mühendisliği öğrencisiyim ve önümüzdeki dönem mezun olacağım. Nasılsınız😊\n\n"
        "1. sınıftan beri P&G, QNB, Pfizer gibi global şirketlerde iş geliştirme, pazarlama, satış gibi alanlarda deneyimler edindim ve mezuniyetim yaklaşırken kariyerimdeki next big thing'i kurguluyorum.\n\n"
        "Mühendislik eğitimim ve kuvvetli business sense'im ile teknoloji odaklı, küçük ve dinamik bir şirkette Growth & Product odaklı bir rol arayışına başladım ve karşıma Hiwell'de AI Agent Operator ilanı çıktı.\n\n"
        "Hiwell'in Boğaziçi Ventures desteğiyle online psikoterapi ve mental sağlık alanında geliştirdiği algoritmik eşleştirme teknolojisi ve küresel pazarlardaki hızlı büyümesi beni çok etkiledi ve bu yolculukta birlikte yapabileceklerimiz olduğunu düşündüğüm için size ulaşıyorum. Tanışmak ve birlikte yapabileceklerimizi keşfetmek çok isterim. İçinde bazı projelerimin olduğu Github hesabımı paylaşıyorum: https://github.com/erdogankocabas2\n\n"
        "CV'mi de ekte paylaşıyorum.\n\n"
        "Çok teşekkürler,\n"
        "Erdoğan"
    )

def main():
    conn = db.get_connection()
    c = conn.cursor()

    hiwell_comp = conn.execute("SELECT id FROM companies WHERE name = 'Hiwell'").fetchone()
    company_id = hiwell_comp["id"] if hiwell_comp else 69

    cv_path = Path("assets/erdogan_kocabas_cv.pdf")
    if not cv_path.exists():
        logger.error("CV file missing")
        sys.exit(1)

    sender_email = os.getenv("GMAIL_SENDER_EMAIL", "").strip()
    app_pwd = os.getenv("GMAIL_APP_PASSWORD", "").strip()
    istanbul_tz = ZoneInfo("Europe/Istanbul")

    print("=" * 60)
    print(f"DISPATCHING HIWELL VERIFIED OUTREACH ({len(RECIPIENTS)} emails, 30s interval)")
    print(f"Sender: {sender_email}")
    print("=" * 60)

    for i, rec in enumerate(RECIPIENTS):
        body = build_body(rec["salutation"])
        subject = "Selam & Tanışma"

        c.execute("""
            INSERT INTO leads (
                company_id, full_name, first_name, title, honorific,
                email, email_verification_status, status, subject, rendered_body, attachment_path, created_at, updated_at
            ) VALUES (?, ?, ?, ?, '', ?, 'VERIFIED', 'APPROVED', ?, ?, 'assets/erdogan_kocabas_cv.pdf', datetime('now'), datetime('now'))
        """, (company_id, rec["name"], rec["salutation"], rec["role"], rec["email"], subject, body))
        lead_id = c.lastrowid
        conn.commit()

        send_id = db.create_send(conn, {
            "campaign_id": 4,
            "lead_id": lead_id,
            "scheduled_at": datetime.now(istanbul_tz).isoformat(),
        })

        try:
            logger.info("[%d/%d] Sending to %s <%s>...", i + 1, len(RECIPIENTS), rec['name'], rec['email'])
            msg_id = smtp_client.send_smtp_email(
                to=rec["email"],
                subject=subject,
                body=body,
                attachment_path="assets/erdogan_kocabas_cv.pdf",
                sender_email=sender_email,
                app_password=app_pwd,
            )

            db.update_send(conn, send_id, {
                "sent_at": datetime.now(istanbul_tz).isoformat(),
                "gmail_message_id": msg_id,
            })
            c.execute("UPDATE leads SET status = 'SENT' WHERE id = ?", (lead_id,))
            conn.commit()
            logger.info("  ✓ SUCCESS — Message ID: %s", msg_id)

        except Exception as e:
            logger.error("  ✗ FAILED: %s", e)
            db.update_send(conn, send_id, {
                "error_code": type(e).__name__,
                "error_message": str(e)[:500],
            })
            c.execute("UPDATE leads SET status = 'FAILED' WHERE id = ?", (lead_id,))
            conn.commit()

        if i < len(RECIPIENTS) - 1:
            logger.info("Pacing 30 seconds...")
            time.sleep(30)

    export()
    print("Hiwell verified outreach completed.")
    conn.close()

if __name__ == "__main__":
    main()
