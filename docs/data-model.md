# Data Model

Use SQLite for the source of truth; Excel is an export only.

## companies
- id
- name
- website
- domain
- sector
- description
- location
- work_mode
- employee_count
- employee_count_confidence
- funding_status
- funding_details
- funding_source_url
- founder_quality_score
- company_potential_score
- sector_fit_score
- funding_traction_score
- total_fit_score
- classification (OUTREACH/WATCHLIST/REJECT)
- rationale
- researched_at

## founders
- id
- company_id
- full_name
- title
- university
- previous_companies
- founder_quality_evidence
- profile_url
- source_urls_json

## leads
- id
- company_id
- full_name
- first_name
- title
- contact_priority
- profile_url
- honorific
- honorific_confidence
- honorific_evidence_url
- email
- email_provider
- email_score
- email_verification_status
- email_source_urls_json
- personalization_paragraph
- personalization_source_urls_json
- subject
- rendered_body
- attachment_path
- eligibility
- status
- created_at
- updated_at

## campaigns
- id
- name
- target_leads
- snapshot_hash
- approved
- approved_at
- scheduled_start
- timezone
- status

## sends
- id
- campaign_id
- lead_id
- scheduled_at
- attempted_at
- sent_at
- gmail_message_id
- error_code
- error_message
