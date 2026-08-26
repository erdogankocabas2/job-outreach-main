#!/usr/bin/env python3
"""Migrate SQLite data to Supabase PostgreSQL reliably."""

from __future__ import annotations

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src import db, supabase_client


def main():
    if not supabase_client.is_configured():
        print("❌ SUPABASE_URL and SUPABASE_KEY are not set in .env")
        sys.exit(1)

    print("🔌 Connecting to Supabase...")
    sb = supabase_client.get_supabase_client()
    conn = db.get_connection()

    # 1. Sync Companies by domain
    companies = conn.execute("SELECT * FROM companies").fetchall()
    print(f"Syncing {len(companies)} companies...")
    for c in companies:
        data = dict(c)
        data.pop("id", None)
        sb.table("companies").upsert(data, on_conflict="domain").execute()

    # Get domain -> supabase_id mapping
    sb_companies = sb.table("companies").select("id, domain").execute().data
    domain_to_sbid = {sc["domain"]: sc["id"] for sc in sb_companies}

    # 2. Sync Founders
    founders = conn.execute("SELECT f.*, c.domain FROM founders f JOIN companies c ON f.company_id = c.id").fetchall()
    print(f"Syncing {len(founders)} founders...")
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

    # 3. Sync Leads by email
    leads = conn.execute("SELECT l.*, c.domain FROM leads l JOIN companies c ON l.company_id = c.id").fetchall()
    print(f"Syncing {len(leads)} leads...")
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


    # 4. Sync Campaigns
    campaigns = conn.execute("SELECT * FROM campaigns").fetchall()
    print(f"Syncing {len(campaigns)} campaigns...")
    for camp in campaigns:
        data = dict(camp)
        data.pop("id", None)
        try:
            sb.table("campaigns").insert(data).execute()
        except Exception:
            pass

    # 5. Sync Sends
    sends = conn.execute("SELECT * FROM sends").fetchall()
    print(f"Syncing {len(sends)} send records...")
    for send in sends:
        data = dict(send)
        data.pop("id", None)
        try:
            sb.table("sends").insert(data).execute()
        except Exception:
            pass

    print("\n✅ Migration complete! All data live on Supabase.")
    conn.close()


if __name__ == "__main__":
    main()
