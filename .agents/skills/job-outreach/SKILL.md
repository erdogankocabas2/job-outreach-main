---
name: job-outreach
description: Builds and operates Erdoğan's Turkish startup job-outreach campaign: company research, founder scoring, contact discovery, email finding/verification, personalization, approval preview, Gmail sending, and Excel export.
---

# Job Outreach Skill

## Use this skill when

The task involves researching candidate companies, selecting contacts, enriching work emails, generating outreach, reviewing a campaign, scheduling/sending mail, or exporting outreach data.

## Workflow

### Phase 0 — Preconditions
1. Read `AGENTS.md`, `config/campaign.yaml`, `templates/email_tr.txt`, and the CV.
2. Confirm required credentials are available without printing them.
3. Initialize/migrate SQLite database.
4. Set campaign approval to `false` unless a matching approved snapshot exists.

### Phase 1 — Company discovery
1. Search the public web for Turkey-focused AI, SaaS, and gaming startups.
2. Prefer companies with <= 50 employees.
3. Gather: name, domain, sector, description, location/work model if public, approximate headcount, funding evidence, founders, founder education, founder prior employers, traction signals, and source URLs.
4. Compute founder quality and company fit score per `AGENTS.md`.
5. Classify:
   - `OUTREACH`: funded + sufficiently strong fit.
   - `WATCHLIST`: not verified as funded but exceptionally promising.
   - `REJECT`: weak fit / >50 employees / wrong sector / insufficient evidence.
6. Do not email `WATCHLIST` companies.

### Phase 2 — Contact discovery
For `OUTREACH` companies, research up to 3 people in this priority:
1. Founder / Co-founder
2. Chief of Staff / Founder's Office
3. People / HR
4. Head of Growth / Product / Business Development

Capture full name, title, public profile URL/source, and evidence that the person currently works there.

### Phase 3 — Honorific decision
Determine `Hanım` or `Bey` only with high confidence from public context. Do not rely on a weak name-only guess when ambiguous.
- Confident: set honorific and continue.
- Uncertain: `NEEDS_GENDER_REVIEW`; do not email.

### Phase 4 — Email discovery and verification
Use this order:
1. Hunter Email Finder (primary).
2. Apollo People Enrichment (optional fallback if configured).
3. Public authoritative company/person source if it explicitly lists a professional email.

Rules:
- Never synthesize `firstname@domain` or any pattern-based guess.
- Record provider, provider score/status, sources, and lookup timestamp.
- Hunter `valid` is eligible.
- `accept_all` is eligible only if `campaign.yaml` threshold permits it.
- `unknown`, `invalid`, disposable, or personal/webmail addresses are not eligible unless explicitly reviewed by the user.

### Phase 5 — Personalization
Use 1–2 short sentences only.
Ground it in one or more concrete facts such as product approach, business model, recent launch, credible traction, or founder/company direction.
Do not use vague filler such as “yenilikçi çalışmalarınız beni çok etkiledi” without a concrete reason.
Store source URL(s) for the paragraph.

### Phase 6 — Email generation
Render exactly from `templates/email_tr.txt`.
Subject must be `Selam & Tanışma`.
Attach `assets/erdogan_kocabas_cv.pdf`.
Validate all variables and attachment before marking `READY_FOR_REVIEW`.

### Phase 7 — 100-lead snapshot and review
1. Build exactly 100 eligible leads if the market provides enough evidence-backed leads.
2. If fewer than 100 can be safely verified, stop and report the exact count and blockers; never lower standards to hit 100.
3. Freeze generated emails into `data/campaign_snapshot.json` with a snapshot hash.
4. Select 5 representative emails and write `exports/review_preview.md`.
5. Present the 5 to the user and request explicit approval.
6. STOP. Do not schedule or send yet.

### Phase 8 — Approval
Only a clear approval such as “onay”, “approved”, or an unambiguous equivalent can set `approved=true`.
If the user requests edits, invalidate the previous approval and snapshot hash.

### Phase 9 — Schedule/send
After approval:
- schedule start: 2026-08-19 10:06 Europe/Istanbul;
- use Gmail API OAuth;
- pace messages using `send_interval_seconds` from config;
- verify the exact frozen message before sending;
- verify CV attachment exists for every message;
- write Gmail message ID and sent timestamp to DB;
- errors must not be silently retried beyond configured retry count.

### Phase 10 — Export
Create/update `exports/job_outreach.xlsx` with all researched companies and leads, including non-sendable statuses and watchlist entries.
