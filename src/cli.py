"""CLI entry points for the job-outreach campaign."""

from __future__ import annotations

import argparse
import json
import logging
import sys
import time
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from . import db, campaign
from .models import CampaignConfig, CampaignStatus, LeadStatus
from .export_xlsx import export

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)


def cmd_init(args):
    """Initialize the database."""
    db.init_db()
    logger.info("Database initialized at %s", db.DB_PATH)

    config = CampaignConfig.from_yaml()
    conn = db.get_connection()

    existing = db.get_latest_campaign(conn)
    if not existing:
        cid = db.create_campaign(conn, {
            "name": config.campaign_name,
            "target_leads": config.target_leads,
            "scheduled_start": config.scheduled_start,
            "timezone": config.timezone,
            "status": CampaignStatus.BUILDING.value,
        })
        logger.info("Created campaign #%d: %s", cid, config.campaign_name)
    else:
        logger.info("Campaign already exists: #%d", existing["id"])

    conn.close()


def cmd_export(args):
    """Generate XLSX export."""
    output = export()
    logger.info("Excel export written to %s", output)


def cmd_freeze(args):
    """Freeze the campaign snapshot."""
    conn = db.get_connection()
    camp = db.get_latest_campaign(conn)
    if not camp:
        logger.error("No campaign found — run init first")
        sys.exit(1)

    snapshot_hash = campaign.freeze_snapshot(conn, camp["id"])
    logger.info("Snapshot frozen — hash: %s", snapshot_hash[:16] + "...")
    conn.close()


def cmd_preview(args):
    """Select and write 5 representative emails for review."""
    conn = db.get_connection()
    camp = db.get_latest_campaign(conn)
    if not camp:
        logger.error("No campaign found")
        sys.exit(1)

    leads = campaign.select_preview(conn, camp["id"], count=5)
    if not leads:
        logger.error("No eligible leads found for preview")
        sys.exit(1)

    preview_path = campaign.write_review_preview(leads)
    logger.info("Review preview written to %s (%d emails)", preview_path, len(leads))
    conn.close()


def cmd_approve(args):
    """Approve the current campaign snapshot."""
    conn = db.get_connection()
    camp = db.get_latest_campaign(conn)
    if not camp:
        logger.error("No campaign found")
        sys.exit(1)

    try:
        campaign.approve_campaign(conn, camp["id"])
        logger.info("Campaign #%d APPROVED", camp["id"])
    except ValueError as e:
        logger.error("Approval failed: %s", e)
        sys.exit(1)
    finally:
        conn.close()


def cmd_send(args):
    """Send approved campaign with pacing."""
    conn = db.get_connection()
    camp = db.get_latest_campaign(conn)
    if not camp:
        logger.error("No campaign found")
        sys.exit(1)

    # Pre-flight checks
    issues = campaign.check_send_preconditions(conn, camp["id"])
    if issues:
        for issue in issues:
            logger.error("Send blocked: %s", issue)
        sys.exit(1)

    config = CampaignConfig.from_yaml()

    # Check timing
    istanbul_tz = ZoneInfo(config.timezone)
    scheduled = datetime.fromisoformat(config.scheduled_start)
    now = datetime.now(istanbul_tz)

    if now < scheduled:
        logger.info(
            "Scheduled start is %s — current time is %s. "
            "Use Antigravity Scheduled Tasks to run at the right time.",
            scheduled.isoformat(),
            now.isoformat(),
        )
        sys.exit(0)

    # Load frozen snapshot
    snapshot = campaign.load_snapshot()
    leads = snapshot["leads"]
    logger.info("Sending %d emails with %ds interval", len(leads), config.send_interval_seconds)

    from . import gmail_client

    service = gmail_client.authenticate()
    sender = config.candidate_name  # or from env

    db.update_campaign(conn, camp["id"], {"status": CampaignStatus.SENDING.value})

    sent_count = 0
    fail_count = 0

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

            msg_id = gmail_client.send_email(
                service=service,
                to=lead["email"],
                subject=lead["subject"],
                body=lead["rendered_body"],
                attachment_path=lead["attachment_path"],
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
            logger.info("[%d/%d] Sent to %s", i + 1, len(leads), lead["email"])

        except Exception as e:
            fail_count += 1
            db.update_send(conn, send_id, {
                "error_code": type(e).__name__,
                "error_message": str(e)[:500],
            })
            conn.execute(
                "UPDATE leads SET status = ? WHERE id = ?",
                (LeadStatus.FAILED.value, lead["id"]),
            )
            conn.commit()
            logger.error("[%d/%d] Failed for %s: %s", i + 1, len(leads), lead["email"], e)

        # Pace sends
        if i < len(leads) - 1:
            time.sleep(config.send_interval_seconds)

    # Final status
    if fail_count == 0:
        db.update_campaign(conn, camp["id"], {"status": CampaignStatus.COMPLETED.value})
        logger.info("Campaign COMPLETED — %d emails sent", sent_count)
    else:
        db.update_campaign(conn, camp["id"], {"status": CampaignStatus.PARTIAL_FAILURE.value})
        logger.warning(
            "Campaign PARTIAL_FAILURE — %d sent, %d failed", sent_count, fail_count
        )

    conn.close()


def main():
    parser = argparse.ArgumentParser(description="Job Outreach Campaign CLI")
    sub = parser.add_subparsers(dest="command")

    sub.add_parser("init", help="Initialize database and campaign")
    sub.add_parser("export", help="Generate XLSX export")
    sub.add_parser("freeze", help="Freeze campaign snapshot")
    sub.add_parser("preview", help="Generate 5-email review preview")
    sub.add_parser("approve", help="Approve the campaign")
    sub.add_parser("send", help="Send approved campaign")

    args = parser.parse_args()

    commands = {
        "init": cmd_init,
        "export": cmd_export,
        "freeze": cmd_freeze,
        "preview": cmd_preview,
        "approve": cmd_approve,
        "send": cmd_send,
    }

    if args.command in commands:
        commands[args.command](args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
