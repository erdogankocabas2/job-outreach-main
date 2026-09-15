#!/usr/bin/env python3
"""Send approved outreach campaign emails using Gmail SMTP App Password with 30s pacing."""

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

from src import campaign, db, smtp_client
from src.export_xlsx import export

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s: %(message)s")
logger = logging.getLogger("send_campaign")


def main():
    conn = db.get_connection()
    camp = db.get_latest_campaign(conn)

    if not camp:
        logger.error("No campaign found in database")
        sys.exit(1)

    if not camp["approved"]:
        logger.error("Campaign is not approved! Cannot send.")
        sys.exit(1)

    snapshot = campaign.load_snapshot()
    leads = snapshot["leads"]
    logger.info("Loaded approved campaign snapshot containing %d leads", len(leads))

    # Verify attachment
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
    db.update_campaign(conn, camp["id"], {"status": "SENDING"})

    sent_count = 0
    fail_count = 0

    print("=" * 60)
    print(f"STARTING GMAIL OUTREACH ({len(leads)} emails, 30s interval)")
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
    db.update_campaign(conn, camp["id"], {"status": "COMPLETED"})
    export()

    print("=" * 60)
    print(f"CAMPAIGN FINISHED: {sent_count} sent, {fail_count} failed")
    print("Excel export and SQLite database updated.")
    print("=" * 60)
    conn.close()


if __name__ == "__main__":
    main()
