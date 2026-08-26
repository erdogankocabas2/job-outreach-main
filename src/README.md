# Runtime implementation target

The Antigravity coding agent should implement modules roughly along these boundaries:

- `db.py` — SQLite schema/migrations/repositories
- `models.py` — Pydantic models and enums
- `research.py` — normalized research ingestion + source tracking
- `scoring.py` — founder/company scoring
- `hunter.py` — Hunter finder/verifier client
- `apollo.py` — optional fallback enrichment client
- `personalize.py` — structured personalization generation/validation
- `render.py` — immutable template renderer
- `gmail_client.py` — OAuth + MIME PDF attachment + messages.send
- `campaign.py` — snapshot, approval and state transitions
- `export_xlsx.py` — Excel generation
- `cli.py` — commands for init/build-preview/approve/send/export

Do not implement sending before approval checks are enforced in code.
