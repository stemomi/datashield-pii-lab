from __future__ import annotations

from pathlib import Path

from app.core.models import EntityType, SanitizationMode, SourceDocument
from app.detectors.regex_detector import detect_with_regex
from app.transformers.masker import mask_value
from app.transformers.redactor import redact_value
from app.transformers.sanitizer import apply_sanitization


def test_mask_value_email() -> None:
    masked = mask_value("mario.rossi@example.it", EntityType.EMAIL)
    assert masked.startswith("m")
    assert masked.endswith("@example.it")


def test_redact_value() -> None:
    assert redact_value("foo", EntityType.IBAN) == "[REDACTED_IBAN]"


def test_apply_sanitization_replaces_values() -> None:
    content = [{"email": "mario.rossi@example.it", "iban": "IT60X0542811101000000123456"}]
    source = SourceDocument(input_path=Path("sample.json"), input_format="json", content=content)
    detections = tuple(detect_with_regex(source))

    result = apply_sanitization(source, detections, SanitizationMode.MASK)

    sanitized_row = result.content[0]
    assert sanitized_row["email"] != "mario.rossi@example.it"
    assert sanitized_row["iban"].startswith("IT")
