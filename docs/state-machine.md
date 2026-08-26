# State Machine

## Company status
- `DISCOVERED`
- `RESEARCHED`
- `OUTREACH`
- `WATCHLIST`
- `REJECT`

## Lead status
- `CONTACT_FOUND`
- `NEEDS_GENDER_REVIEW`
- `EMAIL_NOT_FOUND`
- `EMAIL_UNVERIFIED`
- `INVALID_EMAIL`
- `READY_FOR_REVIEW`
- `IN_PREVIEW`
- `APPROVED`
- `SCHEDULED`
- `SENT`
- `FAILED`
- `SKIPPED_DUPLICATE`

## Campaign status
- `BUILDING`
- `AWAITING_APPROVAL`
- `APPROVED`
- `SCHEDULED`
- `SENDING`
- `COMPLETED`
- `PARTIAL_FAILURE`

## Critical transitions

`READY_FOR_REVIEW -> APPROVED` is impossible until the user explicitly approves the 5-email preview.

`APPROVED -> SCHEDULED` requires:
- matching frozen snapshot hash;
- valid Gmail OAuth;
- CV exists;
- scheduled time is configured.

Any modification to generated emails after approval invalidates approval and returns campaign to `AWAITING_APPROVAL`.
