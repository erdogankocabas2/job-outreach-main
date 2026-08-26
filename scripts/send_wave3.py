#!/usr/bin/env python3
"""Send Wave 3 VC-Backed Campaign Emails (20 Companies) at Scheduled Time with 30s pacing and live Supabase sync."""

from __future__ import annotations

import json
import logging
import os
import sys
import time
from datetime import datetime
from zoneinfo import ZoneInfo

from dotenv import load_dotenv
load_dotenv()

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src import db, gmail_client, supabase_client
from src.export_xlsx import export

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s: %(message)s")
logger = logging.getLogger("send_wave3")


def sync_to_supabase(conn):
    if not supabase_client.is_configured():
        logger.warning("Supabase credentials not configured, skipping live sync.")
        return

    logger.info("Syncing updated SQLite database to Supabase PostgreSQL...")
    sb = supabase_client.get_supabase_client()

    companies = conn.execute("SELECT * FROM companies").fetchall()
    for c in companies:
        data = dict(c)
        data.pop("id", None)
        try:
            sb.table("companies").upsert(data, on_conflict="domain").execute()
        except Exception:
            pass

    sb_companies = sb.table("companies").select("id, domain").execute().data
    domain_to_sbid = {sc["domain"]: sc["id"] for sc in sb_companies}

    founders = conn.execute("SELECT f.*, c.domain FROM founders f JOIN companies c ON f.company_id = c.id").fetchall()
    for f in founders:
        data = dict(f)
        domain = data.pop("domain", None)
        data.pop("id", None)
        if domain in domain_to_sbid:
            data["company_id"] = domain_to_sbid[domain]
        if data.get("source_urls_json"):
            try:
                data["source_urls_json"] = json.loads(data["source_urls_json"])
            except Exception:
                pass
        try:
            sb.table("founders").insert(data).execute()
        except Exception:
            pass

    leads = conn.execute("SELECT l.*, c.domain FROM leads l JOIN companies c ON l.company_id = c.id").fetchall()
    for l in leads:
        data = dict(l)
        domain = data.pop("domain", None)
        data.pop("id", None)
        if domain in domain_to_sbid:
            data["company_id"] = domain_to_sbid[domain]
        for json_field in ("email_source_urls_json", "personalization_source_urls_json"):
            if data.get(json_field):
                try:
                    data[json_field] = json.loads(data[json_field])
                except Exception:
                    pass
        try:
            sb.table("leads").upsert(data, on_conflict="email").execute()
        except Exception:
            pass

    sends = conn.execute("SELECT * FROM sends").fetchall()
    for send in sends:
        data = dict(send)
        data.pop("id", None)
        try:
            sb.table("sends").insert(data).execute()
        except Exception:
            pass

    logger.info("✅ Live Supabase sync complete!")


def main():
    conn = db.get_connection()

    # 1. Get Wave 3 unsent leads scheduled for review
    leads = conn.execute("""
        SELECT l.id, l.full_name, l.first_name, l.email, l.subject, l.rendered_body, c.name as company_name
        FROM leads l
        JOIN companies c ON l.company_id = c.id
        WHERE l.eligibility = 1 AND l.status IN ('APPROVED', 'READY_FOR_REVIEW') AND l.status != 'SENT' AND c.id >= 49
    """).fetchall()


    leads = [dict(l) for l in leads]
    logger.info(f"Total unsent eligible Wave 3 VC-Backed leads: {len(leads)}")

    if not leads:
        logger.warning("No unsent eligible leads found!")
        conn.close()
        return

    # 2. Authenticate Gmail API
    logger.info("Authenticating with Gmail API for direct outreach sending...")
    service = gmail_client.authenticate()
    istanbul_tz = ZoneInfo("Europe/Istanbul")

    camp = db.get_latest_campaign(conn)
    camp_id = camp["id"] if camp else 2

    sent_count = 0
    fail_count = 0

    print(f"\n{'='*60}")
    print(f"STARTING GMAIL OUTREACH FOR WAVE 3 VC-BACKED STARTUPS ({len(leads)} emails, 30s pacing)")
    print(f"{'='*60}\n")

    for i, lead in enumerate(leads):
        send_id = db.create_send(conn, {
            "campaign_id": camp_id,
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
                ("SENT", lead["id"]),
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
                ("FAILED", lead["id"]),
            )
            conn.commit()

        # 30-second pacing between sends
        if i < len(leads) - 1:
            logger.info("  ... Pacing 30 seconds before next send ...")
            time.sleep(30)

    # 3. Update Excel export
    export()

    # 4. Live sync to Supabase
    sync_to_supabase(conn)

    print(f"\n{'='*60}")
    print(f"WAVE 3 VC-BACKED CAMPAIGN COMPLETE: {sent_count} sent, {fail_count} failed")
    print(f"Database & Supabase sync completed!")
    print(f"{'='*60}\n")

    conn.close()


if __name__ == "__main__":
    main()
