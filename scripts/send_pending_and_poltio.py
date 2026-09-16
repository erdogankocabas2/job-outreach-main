#!/usr/bin/env python3
"""Send Poltio general email (info@poltio.com) and any pending corrected leads."""

from __future__ import annotations

import logging
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo
from dotenv import load_dotenv

load_dotenv()
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src import db, smtp_client
from src.export_xlsx import export

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s: %(message)s")
logger = logging.getLogger("send_poltio_and_pending")


def main():
    conn = db.get_connection()
    istanbul_tz = ZoneInfo("Europe/Istanbul")
    sender_email = os.getenv("GMAIL_SENDER_EMAIL", "").strip()
    app_pwd = os.getenv("GMAIL_APP_PASSWORD", "").strip()

    cv_path = Path("assets/erdogan_kocabas_cv.pdf")
    if not cv_path.exists():
        logger.error("CV not found")
        sys.exit(1)

    # 1. First, Poltio (info@poltio.com)
    poltio_comp = conn.execute("SELECT id FROM companies WHERE name = 'Poltio'").fetchone()
    poltio_comp_id = poltio_comp["id"] if poltio_comp else 64

    poltio_body = (
        "Merhaba Poltio Ekibi,\n\n"
        "Ben Erdoğan. Boğaziçi Üniversitesi endüstri mühendisliği öğrencisiyim ve önümüzdeki dönem mezun olacağım. Nasılsınız😊\n\n"
        "1. sınıftan beri P&G, QNB, Pfizer gibi global şirketlerde iş geliştirme, pazarlama, satış gibi alanlarda deneyimler edindim ve mezuniyetim yaklaşırken kariyerimdeki next big thing'i kurguluyorum.\n\n"
        "Mühendislik eğitimim ve kuvvetli business sense'im ile teknoloji odaklı, küçük ve dinamik bir şirkette Growth & Product odaklı bir rol arayışına başladım ve karşıma Poltio çıktı.\n\n"
        "Poltio'nun interaktif anket ve etkileşim araçlarıyla markalara sunduğu zengin tüketici içgörüleri beni çok etkiledi ve bu yolculukta birlikte yapabileceklerimiz olduğunu düşündüğüm için size ulaşıyorum. Tanışmak ve birlikte yapabileceklerimizi keşfetmek çok isterim.\n\n"
        "CV'mi ekte paylaşıyorum.\n\n"
        "Çok teşekkürler,\n"
        "Erdoğan"
    )

    c = conn.cursor()
    c.execute("""
        INSERT INTO leads (
            company_id, full_name, first_name, title, honorific,
            email, email_verification_status, status, subject, rendered_body, attachment_path, created_at, updated_at
        ) VALUES (?, 'Poltio Team', 'Poltio Ekibi', 'Team / Contact', '',
                  'info@poltio.com', 'VERIFIED', 'APPROVED', 'Selam & Tanışma', ?, 'assets/erdogan_kocabas_cv.pdf', datetime('now'), datetime('now'))
    """, (poltio_comp_id, poltio_body))
    poltio_lead_id = c.lastrowid
    conn.commit()

    # List of leads to send: Poltio + the 5 DNS retry leads
    target_lead_ids = [poltio_lead_id, 51, 52, 101, 106, 107]

    leads = conn.execute("""
        SELECT l.id, l.full_name, l.first_name, l.email, l.subject, l.rendered_body, c.name as company_name
        FROM leads l
        JOIN companies c ON l.company_id = c.id
        WHERE l.id IN ({})
        ORDER BY l.id ASC
    """.format(",".join(str(k) for k in target_lead_ids))).fetchall()

    leads = [dict(l) for l in leads]
    logger.info("Sending %d emails...", len(leads))

    for i, lead in enumerate(leads):
        clean_body = lead["rendered_body"].split("# Validation rules")[0].strip()
        send_id = db.create_send(conn, {
            "campaign_id": 4,
            "lead_id": lead["id"],
            "scheduled_at": datetime.now(istanbul_tz).isoformat(),
        })

        try:
            logger.info("[%d/%d] Sending to %s <%s> @ %s...", i + 1, len(leads), lead['full_name'], lead['email'], lead['company_name'])
            msg_id = smtp_client.send_smtp_email(
                to=lead["email"],
                subject=lead["subject"],
                body=clean_body,
                attachment_path="assets/erdogan_kocabas_cv.pdf",
                sender_email=sender_email,
                app_password=app_pwd,
            )
            db.update_send(conn, send_id, {
                "sent_at": datetime.now(istanbul_tz).isoformat(),
                "gmail_message_id": msg_id,
            })
            conn.execute("UPDATE leads SET status = 'SENT', rendered_body = ? WHERE id = ?", (clean_body, lead["id"]))
            conn.commit()
            logger.info("  ✓ SUCCESS — Message ID: %s", msg_id)
        except Exception as e:
            logger.error("  ✗ FAILED to send to %s: %s", lead['email'], e)
            db.update_send(conn, send_id, {
                "error_code": type(e).__name__,
                "error_message": str(e)[:500],
            })
            conn.execute("UPDATE leads SET status = 'FAILED' WHERE id = ?", (lead["id"],))
            conn.commit()

        if i < len(leads) - 1:
            time.sleep(30)

    export()
    print("Done.")
    conn.close()


if __name__ == "__main__":
    main()
