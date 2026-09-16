#!/usr/bin/env python3
"""Resend leads with corrected active domains (bold.games, missioncontrol.gs, agave.games, getheltia.com, appsamurai.com)."""

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
logger = logging.getLogger("resend_domain_corrections")

# Mapping of lead ID to corrected email
CORRECTIONS = {
    21: "alperen@getheltia.com",
    22: "dincer@getheltia.com",
    39: "ulas@bold.games",
    40: "atakan@bold.games",
    41: "candas@bold.games",
    51: "kivanc@missioncontrol.gs",
    52: "murat@missioncontrol.gs",
    101: "seyhmus@appsamurai.com",
    106: "alperen@agave.games",
    107: "oguzhan@agave.games",
}


def main():
    conn = db.get_connection()

    # Update emails and clean body if needed
    for lead_id, new_email in CORRECTIONS.items():
        conn.execute("UPDATE leads SET email = ?, status = 'APPROVED' WHERE id = ?", (new_email, lead_id))
    conn.commit()

    leads = conn.execute("""
        SELECT l.id, l.full_name, l.first_name, l.email, l.subject, l.rendered_body, c.name as company_name
        FROM leads l
        JOIN companies c ON l.company_id = c.id
        WHERE l.id IN ({})
        ORDER BY l.id ASC
    """.format(",".join(str(k) for k in CORRECTIONS.keys()))).fetchall()

    leads = [dict(l) for l in leads]
    logger.info("Found %d domain-corrected leads to dispatch", len(leads))

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
    sent_count = 0
    fail_count = 0

    print("=" * 60)
    print(f"DISPATCHING {len(leads)} CORRECTED EMAILS (30s interval)")
    print(f"Sender: {sender_email}")
    print("=" * 60)

    for i, lead in enumerate(leads):
        # Verify body doesn't have #
        clean_body = lead["rendered_body"].split("# Validation rules")[0].strip()
        
        send_id = db.create_send(conn, {
            "campaign_id": 4, # default campaign
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
                body=clean_body,
                attachment_path="assets/erdogan_kocabas_cv.pdf",
                sender_email=sender_email,
                app_password=app_pwd,
            )

            db.update_send(conn, send_id, {
                "sent_at": datetime.now(istanbul_tz).isoformat(),
                "gmail_message_id": msg_id,
            })

            conn.execute(
                "UPDATE leads SET status = ?, rendered_body = ? WHERE id = ?",
                ("SENT", clean_body, lead["id"]),
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

    export()

    print("=" * 60)
    print(f"DISPATCH COMPLETED: {sent_count} sent, {fail_count} failed")
    print("Excel export and SQLite database updated.")
    print("=" * 60)
    conn.close()


if __name__ == "__main__":
    main()
