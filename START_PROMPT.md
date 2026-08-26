# First prompt to paste into the Antigravity agent

Read the entire workspace, especially `AGENTS.md`, `.agents/skills/job-outreach/SKILL.md`, `config/campaign.yaml`, `templates/email_tr.txt`, and the CV in `assets/erdogan_kocabas_cv.pdf`.

Then implement the minimum reliable Python runtime needed for this project using SQLite as the source of truth, Hunter as the primary email finder/verifier, optional Apollo fallback, Gmail API OAuth for sending, and XLSX export.

After implementation and tests, execute the campaign research workflow:
- research Turkish AI/SaaS/gaming startups with <=50 employees;
- prioritize strong founders defined primarily by strong university + strong company background;
- classify funded fits as OUTREACH and exceptional unfunded companies as WATCHLIST only;
- research up to 3 people/company in this order: Founder/Co-founder → Chief of Staff/Founder's Office → People/HR → Head of Growth/Product/Business Development;
- build 100 verified, send-eligible person-company leads if possible without weakening standards;
- do not guess emails;
- do not email anyone whose Hanım/Bey honorific is uncertain;
- create 1–2 sentence evidence-backed personalization;
- use the locked `Selam & Tanışma` template;
- attach `assets/erdogan_kocabas_cv.pdf` to every email;
- freeze the 100-lead snapshot;
- generate `exports/job_outreach.xlsx`;
- show me exactly 5 representative generated emails for approval.

STOP at the approval gate. Do not send or schedule any email before I explicitly approve the preview. If I approve, the campaign should be scheduled to start at 19 August 2026 10:06 Europe/Istanbul, with paced sending rather than one simultaneous API burst.
