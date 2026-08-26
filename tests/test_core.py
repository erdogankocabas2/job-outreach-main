"""Tests for models, db, scoring, render, and campaign modules."""

import json
import os
import sqlite3
import tempfile
from pathlib import Path

import pytest

# ── Setup ─────────────────────────────────────────────────────────────────

# Ensure we have a template for render tests
TEMPLATE_CONTENT = """SUBJECT: Selam & Tanışma

Merhaba {{first_name}} {{honorific}},

Ben Erdoğan. Boğaziçi Üniversitesi endüstri mühendisliği öğrencisiyim ve önümüzdeki dönem mezun olacağım. Nasılsınız😊

1. sınıftan beri P&G, QNB, Pfizer gibi global şirketlerde iş geliştirme, pazarlama, satış gibi alanlarda deneyimler edindim ve mezuniyetim yaklaşırken kariyerimdeki next big thing'i kurguluyorum.

Mühendislik eğitimim ve kuvvetli business sense'im ile teknoloji odaklı, küçük ve dinamik bir şirkette Growth & Product odaklı bir rol arayışına başladım ve karşıma {{company_name}} çıktı.

{{personalization_paragraph}} beni çok etkiledi ve bu yolculukta birlikte yapabileceklerimiz olduğunu düşündüğüm için size ulaşıyorum. Tanışmak ve birlikte yapabileceklerimizi keşfetmek çok isterim.

CV'mi ekte paylaşıyorum.

Çok teşekkürler,
Erdoğan
"""


@pytest.fixture
def template_file(tmp_path):
    """Create a temporary template file."""
    p = tmp_path / "email_tr.txt"
    p.write_text(TEMPLATE_CONTENT, encoding="utf-8")
    return p


@pytest.fixture
def db_path(tmp_path):
    """Create a temporary database."""
    p = tmp_path / "test.db"
    # Must set the path before importing db
    import src.db as db_mod
    db_mod.init_db(p)
    return p


@pytest.fixture
def conn(db_path):
    """Get a connection to the test database."""
    import src.db as db_mod
    c = db_mod.get_connection(db_path)
    yield c
    c.close()


# ── Test Models ───────────────────────────────────────────────────────────


class TestModels:
    def test_company_status_values(self):
        from src.models import CompanyStatus
        assert CompanyStatus.OUTREACH.value == "OUTREACH"
        assert CompanyStatus.WATCHLIST.value == "WATCHLIST"
        assert CompanyStatus.REJECT.value == "REJECT"

    def test_lead_status_values(self):
        from src.models import LeadStatus
        assert LeadStatus.NEEDS_GENDER_REVIEW.value == "NEEDS_GENDER_REVIEW"
        assert LeadStatus.READY_FOR_REVIEW.value == "READY_FOR_REVIEW"
        assert LeadStatus.APPROVED.value == "APPROVED"
        assert len(LeadStatus) == 12

    def test_campaign_status_values(self):
        from src.models import CampaignStatus
        assert CampaignStatus.BUILDING.value == "BUILDING"
        assert CampaignStatus.AWAITING_APPROVAL.value == "AWAITING_APPROVAL"
        assert len(CampaignStatus) == 7

    def test_honorific_enum(self):
        from src.models import Honorific
        assert Honorific.HANIM.value == "Hanım"
        assert Honorific.BEY.value == "Bey"

    def test_company_model(self):
        from src.models import Company
        c = Company(name="TestCo", domain="test.com", sector="AI")
        assert c.name == "TestCo"
        assert c.id is None

    def test_lead_model(self):
        from src.models import Lead
        lead = Lead(company_id=1, full_name="Test User", first_name="Test")
        assert lead.status is None
        assert lead.eligibility is None


# ── Test DB ───────────────────────────────────────────────────────────────


class TestDB:
    def test_init_creates_tables(self, conn):
        tables = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        ).fetchall()
        table_names = {t["name"] for t in tables}
        assert "companies" in table_names
        assert "founders" in table_names
        assert "leads" in table_names
        assert "campaigns" in table_names
        assert "sends" in table_names

    def test_upsert_company(self, conn):
        import src.db as db_mod
        cid = db_mod.upsert_company(conn, {
            "name": "TestCo",
            "domain": "testco.com",
            "sector": "AI",
            "classification": "OUTREACH",
        })
        assert cid > 0

        # Upsert same domain should update
        cid2 = db_mod.upsert_company(conn, {
            "name": "TestCo Updated",
            "domain": "testco.com",
            "sector": "SaaS",
        })
        assert cid2 == cid

        company = db_mod.get_company_by_domain(conn, "testco.com")
        assert company["name"] == "TestCo Updated"
        assert company["sector"] == "SaaS"

    def test_upsert_lead(self, conn):
        import src.db as db_mod
        cid = db_mod.upsert_company(conn, {
            "name": "TestCo", "domain": "testco.com",
        })
        lid = db_mod.upsert_lead(conn, {
            "company_id": cid,
            "full_name": "Ali Veli",
            "first_name": "Ali",
            "email": "ali@testco.com",
        })
        assert lid > 0

    def test_duplicate_email_detection(self, conn):
        import src.db as db_mod
        cid = db_mod.upsert_company(conn, {
            "name": "Co1", "domain": "co1.com",
        })
        db_mod.upsert_lead(conn, {
            "company_id": cid,
            "full_name": "Lead 1",
            "first_name": "Lead",
            "email": "same@co1.com",
        })
        assert db_mod.check_duplicate_email(conn, "same@co1.com") is True
        assert db_mod.check_duplicate_email(conn, "different@co1.com") is False

    def test_duplicate_person_detection(self, conn):
        import src.db as db_mod
        cid = db_mod.upsert_company(conn, {
            "name": "Co1", "domain": "co1.com",
        })
        db_mod.upsert_lead(conn, {
            "company_id": cid,
            "full_name": "Same Person",
            "first_name": "Same",
        })
        assert db_mod.check_duplicate_person(conn, "Same Person", cid) is True
        assert db_mod.check_duplicate_person(conn, "Different Person", cid) is False

    def test_campaign_crud(self, conn):
        import src.db as db_mod
        cid = db_mod.create_campaign(conn, {
            "name": "test-campaign",
            "target_leads": 100,
            "status": "BUILDING",
        })
        assert cid > 0

        campaign = db_mod.get_campaign(conn, cid)
        assert campaign["name"] == "test-campaign"
        assert campaign["approved"] == 0

        db_mod.update_campaign(conn, cid, {"approved": 1})
        campaign = db_mod.get_campaign(conn, cid)
        assert campaign["approved"] == 1


# ── Test Scoring ──────────────────────────────────────────────────────────


class TestScoring:
    def test_perfect_score(self):
        from src.scoring import score_company
        score = score_company(100, 100, 100, 100)
        assert score == 100.0

    def test_zero_score(self):
        from src.scoring import score_company
        score = score_company(0, 0, 0, 0)
        assert score == 0.0

    def test_weighted_calculation(self):
        from src.scoring import score_company
        # 80*.35 + 70*.30 + 60*.20 + 50*.15 = 28+21+12+7.5 = 68.5
        score = score_company(80, 70, 60, 50)
        assert score == 68.5

    def test_classify_funded_high(self):
        from src.scoring import classify_company
        from src.models import CompanyStatus
        result = classify_company(70.0, "Series A")
        assert result == CompanyStatus.OUTREACH

    def test_classify_unfunded_high(self):
        from src.scoring import classify_company
        from src.models import CompanyStatus
        result = classify_company(65.0, "unfunded")
        assert result == CompanyStatus.WATCHLIST

    def test_classify_funded_low(self):
        from src.scoring import classify_company
        from src.models import CompanyStatus
        result = classify_company(30.0, "Seed")
        assert result == CompanyStatus.REJECT

    def test_classify_unfunded_low(self):
        from src.scoring import classify_company
        from src.models import CompanyStatus
        result = classify_company(40.0, "unfunded")
        assert result == CompanyStatus.REJECT


# ── Test Render ───────────────────────────────────────────────────────────


class TestRender:
    def test_render_valid(self, template_file):
        from src.render import render_email
        subject, body = render_email(
            first_name="Mehmet",
            honorific="Bey",
            company_name="TestAI",
            personalization_paragraph="Yapay zeka tabanlı müşteri analitiği platformunuz",
            template_path=template_file,
        )
        assert subject == "Selam & Tanışma"
        assert "Mehmet Bey" in body
        assert "TestAI" in body
        assert "Yapay zeka tabanlı" in body

    def test_render_invalid_honorific(self, template_file):
        from src.render import render_email, TemplateValidationError
        with pytest.raises(TemplateValidationError, match="honorific"):
            render_email(
                first_name="Mehmet",
                honorific="Mr",
                company_name="TestAI",
                personalization_paragraph="Test sentence.",
                template_path=template_file,
            )

    def test_render_empty_personalization(self, template_file):
        from src.render import render_email, TemplateValidationError
        with pytest.raises(TemplateValidationError, match="personalization"):
            render_email(
                first_name="Mehmet",
                honorific="Bey",
                company_name="TestAI",
                personalization_paragraph="",
                template_path=template_file,
            )

    def test_validate_attachment(self):
        from src.render import validate_attachment
        # The real CV exists
        assert validate_attachment("assets/erdogan_kocabas_cv.pdf") is True
        assert validate_attachment("nonexistent.pdf") is False


# ── Test Campaign ─────────────────────────────────────────────────────────


class TestCampaign:
    def test_freeze_and_verify(self, conn, tmp_path):
        import src.db as db_mod
        import src.campaign as camp_mod

        # Override paths for test
        camp_mod.SNAPSHOT_PATH = tmp_path / "snapshot.json"

        # Create campaign and eligible lead
        camp_id = db_mod.create_campaign(conn, {
            "name": "test", "target_leads": 1, "status": "BUILDING",
        })
        cid = db_mod.upsert_company(conn, {
            "name": "Co", "domain": "co.com", "classification": "OUTREACH",
            "total_fit_score": 80,
        })
        db_mod.upsert_lead(conn, {
            "company_id": cid,
            "full_name": "Test Lead",
            "first_name": "Test",
            "email": "test@co.com",
            "email_verification_status": "valid",
            "honorific": "Bey",
            "eligibility": 1,
            "status": "READY_FOR_REVIEW",
            "subject": "Selam & Tanışma",
            "rendered_body": "test body",
        })

        snapshot_hash = camp_mod.freeze_snapshot(conn, camp_id)
        assert len(snapshot_hash) == 64  # SHA-256 hex
        assert camp_mod.verify_snapshot_hash(camp_mod.SNAPSHOT_PATH, snapshot_hash)

    def test_approve_requires_snapshot(self, conn):
        import src.db as db_mod
        import src.campaign as camp_mod

        camp_id = db_mod.create_campaign(conn, {
            "name": "test", "status": "BUILDING",
        })

        with pytest.raises(ValueError, match="snapshot"):
            camp_mod.approve_campaign(conn, camp_id)
