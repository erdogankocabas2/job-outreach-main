---
title: Send Approved Job Outreach Campaign
description: Schedule or send only an already approved frozen campaign snapshot.
---

1. Load campaign state and frozen snapshot hash.
2. Verify `approved=true` and that approval matches the current snapshot hash.
3. Verify current time and timezone.
4. Verify Gmail OAuth works and sender identity matches configuration.
5. Verify CV attachment exists.
6. If before 2026-08-19 10:06 Europe/Istanbul, create an Antigravity Scheduled Task for that exact start minute.
7. If at/after the approved start time, send the frozen eligible emails with configured pacing.
8. Persist Gmail message IDs, timestamps, failures, and statuses.
9. Regenerate Excel export.
10. Never send leads marked WATCHLIST, NEEDS_GENDER_REVIEW, INVALID_EMAIL, or otherwise ineligible.
