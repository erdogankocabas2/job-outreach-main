#!/usr/bin/env python3
"""Send Wave 7 Campaign emails (35 leads) using Gmail SMTP App Password with 30s pacing."""

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
logger = logging.getLogger("send_wave7_tech")


def main():
    conn = db.get_connection()
    camp = conn.execute("SELECT * FROM campaigns WHERE name LIKE 'Wave 7%' ORDER BY id DESC LIMIT 1").fetchone()

    if not camp:
        logger.error("No Wave 7 campaign found in database")
        sys.exit(1)

    leads = conn.execute("""
        SELECT l.id, l.full_name, l.first_name, l.email, l.subject, l.rendered_body, c.name as company_name
        FROM leads l
        JOIN companies c ON l.company_id = c.id
        WHERE l.status = 'APPROVED' AND l.id >= 92
        ORDER BY l.id ASC
    """).fetchall()

    leads = [dict(l) for l in leads]
    logger.info("Found %d unsent Wave 7 leads to dispatch", len(leads))

    cv_path = Path("assets/erdogan_kocabas_cv.pdf")
    if not cv_path.exists():
        logger.error("Required CV attachment not found at %s", cv_path)
        sys.exit(1)

    sender_email = os.getenv("GMAIL_SENDER_EMAIL", "").strip()
    app_pwd = os.getenv("GMAIL_APP_PASSWORD", "").strip()

    if not sender_email or not app_pwd:
        logger.error("GMAIL_SENDER_EMAIL and GMAIL_APP_PASSWORD must be set in .env")
        sys.exit(1)

    istanbul_tz = ZoneInfo("Europe/Istanbul")
    conn.execute("UPDATE campaigns SET status = 'SENDING' WHERE id = ?", (camp["id"],))
    conn.commit()

    sent_count = 0
    fail_count = 0

    print("=" * 60)
    print(f"STARTING WAVE 7 CAMPAIGN ({len(leads)} emails, 30s interval)")
    print(f"Sender: {sender_email}")
    print("=" * 60)

    for i, lead in enumerate(leads):
        send_id = db.create_send(conn, {
            "campaign_id": camp["id"],
            "lead_id": lead["id"],
            "scheduled_at": datetime.now(istanbul_tz).isoformat(),
        })

        try:
            db.update_send(conn, send_id, {
                "attempted_at": datetime.now(istanbul_tz).isoformat(),
            })

            logger.info(
                "[%d/%d] Sending email to %s <%s> @ %s...",
                i + 1, len(leads), lead['full_name'], lead['email'], lead['company_name']
            )

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

            conn.execute(
                "UPDATE leads SET status = ? WHERE id = ?",
                ("SENT", lead["id"]),
            )
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
            conn.execute(
                "UPDATE leads SET status = ? WHERE id = ?",
                ("FAILED", lead["id"]),
            )
            conn.commit()

        if i < len(leads) - 1:
            logger.info("  ... Pacing 30 seconds before next send ...")
            time.sleep(30)

    # Mark campaign completed
    conn.execute("UPDATE campaigns SET status = 'COMPLETED' WHERE id = ?", (camp["id"],))
    conn.commit()
    export()

    print("=" * 60)
    print(f"WAVE 7 CAMPAIGN COMPLETED: {sent_count} sent, {fail_count} failed")
    print("Excel export and SQLite database updated.")
    print("=" * 60)
    conn.close()


if __name__ == "__main__":
    main()
