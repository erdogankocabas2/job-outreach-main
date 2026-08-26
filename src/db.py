"""SQLite database layer — schema, migrations, and repository functions."""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

DB_PATH = Path("data/job_outreach.db")


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def get_connection(db_path: Path | str = DB_PATH) -> sqlite3.Connection:
    """Return a connection with WAL mode and foreign keys enabled."""
    db_path = Path(db_path)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path))
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    conn.row_factory = sqlite3.Row
    return conn


def init_db(db_path: Path | str = DB_PATH) -> None:
    """Create all tables if they do not exist."""
    conn = get_connection(db_path)
    conn.executescript("""
    CREATE TABLE IF NOT EXISTS companies (
        id                      INTEGER PRIMARY KEY AUTOINCREMENT,
        name                    TEXT NOT NULL,
        website                 TEXT,
        domain                  TEXT UNIQUE,
        sector                  TEXT,
        description             TEXT,
        location                TEXT,
        work_mode               TEXT,
        employee_count          INTEGER,
        employee_count_confidence TEXT,
        funding_status          TEXT,
        funding_details         TEXT,
        funding_source_url      TEXT,
        founder_quality_score   REAL,
        company_potential_score REAL,
        sector_fit_score        REAL,
        funding_traction_score  REAL,
        total_fit_score         REAL,
        classification          TEXT DEFAULT 'DISCOVERED',
        rationale               TEXT,
        researched_at           TEXT
    );

    CREATE TABLE IF NOT EXISTS founders (
        id                      INTEGER PRIMARY KEY AUTOINCREMENT,
        company_id              INTEGER NOT NULL REFERENCES companies(id),
        full_name               TEXT NOT NULL,
        title                   TEXT,
        university              TEXT,
        previous_companies      TEXT,
        founder_quality_evidence TEXT,
        profile_url             TEXT,
        source_urls_json        TEXT
    );

    CREATE TABLE IF NOT EXISTS leads (
        id                             INTEGER PRIMARY KEY AUTOINCREMENT,
        company_id                     INTEGER NOT NULL REFERENCES companies(id),
        full_name                      TEXT NOT NULL,
        first_name                     TEXT NOT NULL,
        title                          TEXT,
        contact_priority               TEXT,
        profile_url                    TEXT,
        honorific                      TEXT,
        honorific_confidence           TEXT,
        honorific_evidence_url         TEXT,
        email                          TEXT,
        email_provider                 TEXT,
        email_score                    REAL,
        email_verification_status      TEXT,
        email_source_urls_json         TEXT,
        personalization_paragraph      TEXT,
        personalization_source_urls_json TEXT,
        subject                        TEXT,
        rendered_body                  TEXT,
        attachment_path                TEXT,
        eligibility                    INTEGER DEFAULT 0,
        status                         TEXT DEFAULT 'CONTACT_FOUND',
        created_at                     TEXT,
        updated_at                     TEXT
    );

    CREATE TABLE IF NOT EXISTS campaigns (
        id              INTEGER PRIMARY KEY AUTOINCREMENT,
        name            TEXT NOT NULL,
        target_leads    INTEGER DEFAULT 100,
        snapshot_hash   TEXT,
        approved        INTEGER DEFAULT 0,
        approved_at     TEXT,
        scheduled_start TEXT,
        timezone        TEXT DEFAULT 'Europe/Istanbul',
        status          TEXT DEFAULT 'BUILDING'
    );

    CREATE TABLE IF NOT EXISTS sends (
        id              INTEGER PRIMARY KEY AUTOINCREMENT,
        campaign_id     INTEGER NOT NULL REFERENCES campaigns(id),
        lead_id         INTEGER NOT NULL REFERENCES leads(id),
        scheduled_at    TEXT,
        attempted_at    TEXT,
        sent_at         TEXT,
        gmail_message_id TEXT,
        error_code      TEXT,
        error_message   TEXT
    );

    CREATE UNIQUE INDEX IF NOT EXISTS idx_leads_email
        ON leads(email) WHERE email IS NOT NULL;
    CREATE INDEX IF NOT EXISTS idx_leads_company
        ON leads(company_id);
    CREATE INDEX IF NOT EXISTS idx_founders_company
        ON founders(company_id);
    """)
    conn.commit()
    conn.close()


# ── Company CRUD ──────────────────────────────────────────────────────────


def upsert_company(conn: sqlite3.Connection, data: dict) -> int:
    """Insert or update a company by domain. Returns the company id."""
    data.setdefault("researched_at", _now_iso())
    existing = conn.execute(
        "SELECT id FROM companies WHERE domain = ?", (data.get("domain"),)
    ).fetchone()

    if existing:
        cid = existing["id"]
        sets = ", ".join(f"{k} = ?" for k in data if k != "id")
        vals = [v for k, v in data.items() if k != "id"]
        vals.append(cid)
        conn.execute(f"UPDATE companies SET {sets} WHERE id = ?", vals)
        conn.commit()
        return cid
    else:
        cols = ", ".join(data.keys())
        placeholders = ", ".join("?" for _ in data)
        cur = conn.execute(
            f"INSERT INTO companies ({cols}) VALUES ({placeholders})",
            list(data.values()),
        )
        conn.commit()
        return cur.lastrowid


def get_company_by_domain(conn: sqlite3.Connection, domain: str) -> Optional[dict]:
    row = conn.execute("SELECT * FROM companies WHERE domain = ?", (domain,)).fetchone()
    return dict(row) if row else None


def get_companies_by_classification(
    conn: sqlite3.Connection, classification: str
) -> list[dict]:
    rows = conn.execute(
        "SELECT * FROM companies WHERE classification = ?", (classification,)
    ).fetchall()
    return [dict(r) for r in rows]


def get_all_companies(conn: sqlite3.Connection) -> list[dict]:
    rows = conn.execute("SELECT * FROM companies ORDER BY total_fit_score DESC").fetchall()
    return [dict(r) for r in rows]


# ── Founder CRUD ──────────────────────────────────────────────────────────


def upsert_founder(conn: sqlite3.Connection, data: dict) -> int:
    """Insert or update a founder by (company_id, full_name)."""
    existing = conn.execute(
        "SELECT id FROM founders WHERE company_id = ? AND full_name = ?",
        (data["company_id"], data["full_name"]),
    ).fetchone()

    if existing:
        fid = existing["id"]
        sets = ", ".join(f"{k} = ?" for k in data if k not in ("id", "company_id", "full_name"))
        vals = [v for k, v in data.items() if k not in ("id", "company_id", "full_name")]
        vals.append(fid)
        if sets:
            conn.execute(f"UPDATE founders SET {sets} WHERE id = ?", vals)
            conn.commit()
        return fid
    else:
        cols = ", ".join(data.keys())
        placeholders = ", ".join("?" for _ in data)
        cur = conn.execute(
            f"INSERT INTO founders ({cols}) VALUES ({placeholders})",
            list(data.values()),
        )
        conn.commit()
        return cur.lastrowid


def get_founders_for_company(conn: sqlite3.Connection, company_id: int) -> list[dict]:
    rows = conn.execute(
        "SELECT * FROM founders WHERE company_id = ?", (company_id,)
    ).fetchall()
    return [dict(r) for r in rows]


# ── Lead CRUD ─────────────────────────────────────────────────────────────


def upsert_lead(conn: sqlite3.Connection, data: dict) -> int:
    """Insert or update a lead by (company_id, full_name) or by email."""
    data.setdefault("created_at", _now_iso())
    data["updated_at"] = _now_iso()

    existing = conn.execute(
        "SELECT id FROM leads WHERE company_id = ? AND full_name = ?",
        (data["company_id"], data["full_name"]),
    ).fetchone()

    if not existing and data.get("email"):
        existing = conn.execute(
            "SELECT id FROM leads WHERE email = ?",
            (data["email"],),
        ).fetchone()

    if existing:
        lid = existing["id"]
        sets = ", ".join(f"{k} = ?" for k in data if k not in ("id", "company_id", "full_name"))
        vals = [v for k, v in data.items() if k not in ("id", "company_id", "full_name")]
        vals.append(lid)
        if sets:
            conn.execute(f"UPDATE leads SET {sets} WHERE id = ?", vals)
            conn.commit()
        return lid
    else:
        try:
            cols = ", ".join(data.keys())
            placeholders = ", ".join("?" for _ in data)
            cur = conn.execute(
                f"INSERT INTO leads ({cols}) VALUES ({placeholders})",
                list(data.values()),
            )
            conn.commit()
            return cur.lastrowid
        except sqlite3.IntegrityError:
            # Handle duplicate email fallback
            if data.get("email"):
                existing = conn.execute(
                    "SELECT id FROM leads WHERE email = ?",
                    (data["email"],),
                ).fetchone()
                if existing:
                    return existing["id"]
            raise



def check_duplicate_email(conn: sqlite3.Connection, email: str, exclude_lead_id: int = 0) -> bool:
    """Return True if an email already exists for a different lead."""
    row = conn.execute(
        "SELECT id FROM leads WHERE email = ? AND id != ?", (email, exclude_lead_id)
    ).fetchone()
    return row is not None


def check_duplicate_person(
    conn: sqlite3.Connection, full_name: str, company_id: int, exclude_lead_id: int = 0
) -> bool:
    """Return True if a person already exists for the same company."""
    row = conn.execute(
        "SELECT id FROM leads WHERE full_name = ? AND company_id = ? AND id != ?",
        (full_name, company_id, exclude_lead_id),
    ).fetchone()
    return row is not None


def get_eligible_leads(conn: sqlite3.Connection) -> list[dict]:
    """Return leads that are send-eligible (eligibility=1) from OUTREACH companies."""
    rows = conn.execute("""
        SELECT l.*, c.name as company_name, c.domain as company_domain,
               c.sector as company_sector, c.classification as company_classification
        FROM leads l
        JOIN companies c ON l.company_id = c.id
        WHERE l.eligibility = 1
          AND c.classification = 'OUTREACH'
          AND l.status IN ('READY_FOR_REVIEW', 'IN_PREVIEW', 'APPROVED', 'SCHEDULED')
        ORDER BY c.total_fit_score DESC
    """).fetchall()
    return [dict(r) for r in rows]


def get_all_leads_for_export(conn: sqlite3.Connection) -> list[dict]:
    """Return all leads with company/founder data for Excel export."""
    rows = conn.execute("""
        SELECT
            c.name       AS company_name,
            c.website    AS company_website,
            c.sector     AS company_sector,
            c.employee_count,
            c.funding_status,
            c.funding_details,
            c.total_fit_score AS company_fit_score,
            c.classification AS company_classification,
            c.founder_quality_score,
            l.full_name  AS person_name,
            l.title      AS person_title,
            l.contact_priority,
            l.profile_url,
            l.honorific,
            l.honorific_confidence,
            l.email,
            l.email_provider AS email_source,
            l.email_verification_status,
            l.email_score,
            l.personalization_paragraph,
            l.personalization_source_urls_json AS personalization_sources,
            l.eligibility AS send_eligible,
            l.status,
            l.attachment_path
        FROM leads l
        JOIN companies c ON l.company_id = c.id
        ORDER BY c.total_fit_score DESC, l.contact_priority
    """).fetchall()
    return [dict(r) for r in rows]


# ── Campaign CRUD ─────────────────────────────────────────────────────────


def create_campaign(conn: sqlite3.Connection, data: dict) -> int:
    cols = ", ".join(data.keys())
    placeholders = ", ".join("?" for _ in data)
    cur = conn.execute(
        f"INSERT INTO campaigns ({cols}) VALUES ({placeholders})",
        list(data.values()),
    )
    conn.commit()
    return cur.lastrowid


def update_campaign(conn: sqlite3.Connection, campaign_id: int, data: dict) -> None:
    sets = ", ".join(f"{k} = ?" for k in data)
    vals = list(data.values()) + [campaign_id]
    conn.execute(f"UPDATE campaigns SET {sets} WHERE id = ?", vals)
    conn.commit()


def get_campaign(conn: sqlite3.Connection, campaign_id: int) -> Optional[dict]:
    row = conn.execute("SELECT * FROM campaigns WHERE id = ?", (campaign_id,)).fetchone()
    return dict(row) if row else None


def get_latest_campaign(conn: sqlite3.Connection) -> Optional[dict]:
    row = conn.execute("SELECT * FROM campaigns ORDER BY id DESC LIMIT 1").fetchone()
    return dict(row) if row else None


# ── Send CRUD ─────────────────────────────────────────────────────────────


def create_send(conn: sqlite3.Connection, data: dict) -> int:
    cols = ", ".join(data.keys())
    placeholders = ", ".join("?" for _ in data)
    cur = conn.execute(
        f"INSERT INTO sends ({cols}) VALUES ({placeholders})",
        list(data.values()),
    )
    conn.commit()
    return cur.lastrowid


def update_send(conn: sqlite3.Connection, send_id: int, data: dict) -> None:
    sets = ", ".join(f"{k} = ?" for k in data)
    vals = list(data.values()) + [send_id]
    conn.execute(f"UPDATE sends SET {sets} WHERE id = ?", vals)
    conn.commit()


def get_sends_for_campaign(conn: sqlite3.Connection, campaign_id: int) -> list[dict]:
    rows = conn.execute(
        "SELECT * FROM sends WHERE campaign_id = ?", (campaign_id,)
    ).fetchall()
    return [dict(r) for r in rows]
