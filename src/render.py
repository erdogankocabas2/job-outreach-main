"""Immutable email template renderer.

Loads templates/email_tr.txt and renders with only the allowed variables.
Subject is always 'Selam & Tanışma' — immutable.
"""

from __future__ import annotations

import re
from pathlib import Path

TEMPLATE_PATH = Path("templates/email_tr.txt")

# Allowed template variables
ALLOWED_VARS = {"first_name", "honorific", "company_name", "personalization_paragraph"}
VALID_HONORIFICS = {"Hanım", "Bey"}
IMMUTABLE_SUBJECT = "Selam & Tanışma"
REQUIRED_ATTACHMENT = "assets/erdogan_kocabas_cv.pdf"


class TemplateValidationError(Exception):
    """Raised when template variables fail validation."""
    pass


def load_template(path: Path | str = TEMPLATE_PATH) -> tuple[str, str]:
    """Load the template file and return (subject_line, body_template).

    Lines starting with # are validation comments and are stripped.
    """
    text = Path(path).read_text(encoding="utf-8")
    lines = text.strip().split("\n")

    # Extract subject from first line
    subject_line = lines[0]
    if not subject_line.startswith("SUBJECT:"):
        raise TemplateValidationError("Template must start with 'SUBJECT: ...'")
    subject = subject_line.replace("SUBJECT:", "").strip()

    # Body is everything after the subject line, excluding comment lines
    body_lines = [l for l in lines[1:] if not l.startswith("#")]
    body = "\n".join(body_lines).strip()

    return subject, body


def validate_variables(
    first_name: str,
    honorific: str,
    company_name: str,
    personalization_paragraph: str,
) -> list[str]:
    """Validate template variables. Returns list of error messages (empty = valid)."""
    errors = []

    if not first_name or not first_name.strip():
        errors.append("first_name is required")

    if honorific not in VALID_HONORIFICS:
        errors.append(f"honorific must be one of {VALID_HONORIFICS}, got '{honorific}'")

    if not company_name or not company_name.strip():
        errors.append("company_name is required")

    if not personalization_paragraph or not personalization_paragraph.strip():
        errors.append("personalization_paragraph is required")
    else:
        # 1-2 sentences: split by sentence-ending punctuation
        sentences = [s.strip() for s in re.split(r'[.!?।]+', personalization_paragraph) if s.strip()]
        if len(sentences) > 3:
            errors.append(
                f"personalization_paragraph should be 1-2 sentences, got ~{len(sentences)}"
            )
        if "\n" in personalization_paragraph:
            errors.append("personalization_paragraph should not contain line breaks")

    return errors


def render_email(
    first_name: str,
    honorific: str,
    company_name: str,
    personalization_paragraph: str,
    *,
    template_path: Path | str = TEMPLATE_PATH,
) -> tuple[str, str]:
    """Render the email template with the given variables.

    Returns (subject, rendered_body).
    Raises TemplateValidationError if validation fails.
    """
    errors = validate_variables(first_name, honorific, company_name, personalization_paragraph)
    if errors:
        raise TemplateValidationError(f"Template validation failed: {'; '.join(errors)}")

    subject, body_template = load_template(template_path)

    # Subject is immutable
    if subject != IMMUTABLE_SUBJECT:
        raise TemplateValidationError(f"Subject must be '{IMMUTABLE_SUBJECT}', got '{subject}'")

    # Render body
    rendered = body_template.replace("{{first_name}}", first_name)
    rendered = rendered.replace("{{honorific}}", honorific)
    rendered = rendered.replace("{{company_name}}", company_name)
    rendered = rendered.replace("{{personalization_paragraph}}", personalization_paragraph)

    # Verify no unresolved placeholders remain
    remaining = re.findall(r"\{\{(\w+)\}\}", rendered)
    if remaining:
        raise TemplateValidationError(f"Unresolved template variables: {remaining}")

    return subject, rendered


def validate_attachment(attachment_path: str = REQUIRED_ATTACHMENT) -> bool:
    """Check that the CV attachment file exists."""
    return Path(attachment_path).exists()
