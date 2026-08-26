#!/usr/bin/env python3
"""Send approved outreach campaign emails now as requested by user.

Enforces:
- Approval check (campaign approved = 1)
- Snapshot hash integrity check
- CV attachment existence (assets/erdogan_kocabas_cv.pdf)
- Gmail OAuth authentication via credentials/client_secret.json
- Database update with Gmail Message IDs, sent timestamps, and statuses
- 30-second interval pacing between sends
"""

from __future__ import annotations

import logging
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

from src import campaign, db, gmail_client
from src.models import CampaignConfig, CampaignStatus, LeadStatus

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s: %(message)s")
logger = logging.getLogger("send_now")


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
    logger.info(f"Loaded approved campaign snapshot containing {len(leads)} leads")

    # Verify snapshot integrity
    if not campaign.verify_snapshot_hash(expected_hash=camp["snapshot_hash"]):
        logger.error("Snapshot hash mismatch! Integrity check failed.")
        sys.exit(1)

    # Verify CV attachment
    cv_path = Path("assets/erdogan_kocabas_cv.pdf")
    if not cv_path.exists():
        logger.error(f"Required CV attachment not found at {cv_path}")
        sys.exit(1)

    logger.info("Authenticating with Gmail API OAuth...")
    service = gmail_client.authenticate()

    istanbul_tz = ZoneInfo("Europe/Istanbul")
    db.update_campaign(conn, camp["id"], {"status": CampaignStatus.SENDING.value})

    sent_count = 0
    fail_count = 0

    print(f"\n{'='*60}")
    print(f"STARTING GMAIL CAMPAIGN SEND ({len(leads)} emails, 30s interval)")
    print(f"{'='*60}\n")

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
                f"[{i+1}/{len(leads)}] Sending email to {lead['full_name']} <{lead['email']}> @ {lead['company_name']}..."
            )

            msg_id = gmail_client.send_email(
                service=service,
                to=lead["email"],
                subject=lead["subject"],
                body=lead["rendered_body"],
                attachment_path="assets/erdogan_kocabas_cv.pdf",
            )

            db.update_send(conn, send_id, {
                "sent_at": datetime.now(istanbul_tz).isoformat(),
                "gmail_message_id": msg_id,
            })

            conn.execute(
                "UPDATE leads SET status = ? WHERE id = ?",
                (LeadStatus.SENT.value, lead["id"]),
            )
            conn.commit()

            sent_count += 1
            logger.info(f"  ✓ SUCCESS — Gmail Message ID: {msg_id}")

        except Exception as e:
            fail_count += 1
            logger.error(f"  ✗ FAILED to send to {lead['email']}: {e}")
            db.update_send(conn, send_id, {
                "error_code": type(e).__name__,
                "error_message": str(e)[:500],
            })
            conn.execute(
                "UPDATE leads SET status = ? WHERE id = ?",
                (LeadStatus.FAILED.value, lead["id"]),
            )
            conn.commit()

        # 30-second pacing between emails
        if i < len(leads) - 1:
            logger.info("  ... Pacing 30 seconds before next send ...")
            time.sleep(30)

    # Final campaign status
    final_status = CampaignStatus.COMPLETED.value if fail_count == 0 else CampaignStatus.PARTIAL_FAILURE.value
    db.update_campaign(conn, camp["id"], {"status": final_status})

    print(f"\n{'='*60}")
    print(f"CAMPAIGN SEND COMPLETE: {sent_count} sent, {fail_count} failed")
    print(f"{'='*60}\n")

    conn.close()


if __name__ == "__main__":
    main()
