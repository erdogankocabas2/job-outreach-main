# job-outreach

Agent-driven Turkish startup job outreach for Erdoğan.

## What this project does

1. Researches Turkey-focused AI/SaaS/gaming startups with <= 50 employees.
2. Scores founder quality and company fit.
3. Keeps exceptional unfunded companies on a watchlist but does not email them.
4. Finds up to 3 relevant people per company in the configured priority order.
5. Finds and verifies professional email addresses.
6. Quarantines uncertain gender/honorific cases for manual review.
7. Generates a short evidence-backed personalization inside a locked Turkish template.
8. Builds a 100-lead frozen campaign snapshot.
9. Shows exactly 5 emails for user approval.
10. Only after explicit approval schedules the campaign for 19 Aug 2026, 10:06 Europe/Istanbul.
11. Sends through the user's Gmail with the CV attached.
12. Exports all research/results to Excel.

## Antigravity setup

Open this folder as the Antigravity Project workspace. Antigravity supports workspace agents under `.agents/agents/`, skills under `.agents/skills/`, rules under `.agents/rules/`, and workflows as markdown customizations.

Select the `job-outreach` custom agent if available, or tell the existing agent:

> Read AGENTS.md and execute the build-campaign workflow. Build the full campaign but stop at the five-email approval gate. Do not send or schedule anything yet.

## API setup

### Required for v1
- Hunter API key: work-email finding + verification.
- Gmail OAuth Desktop App credential: sending.

### Optional fallback
- Apollo API key: fallback person/email enrichment when Hunter cannot return an eligible professional email.

Company and founder discovery can use Antigravity's web-search/browser capabilities, so a separate search API is not required for v1.

## First run

1. Copy `.env.example` to `.env` and fill local credentials.
2. Put Google OAuth desktop client secret at `credentials/client_secret.json`.
3. Keep `assets/erdogan_kocabas_cv.pdf` unchanged.
4. Ask the Antigravity agent to implement the Python runtime described by the docs and then run `/build-campaign` (or execute the equivalent workflow manually).
5. Review the generated `exports/review_preview.md`.
6. Explicitly approve or request changes.
7. Only after approval, run the approved-campaign workflow to schedule/send.

## Important

The campaign time is intentionally an approval-gated requirement, not an already-created schedule. The agent must not create a scheduled task before explicit approval.
