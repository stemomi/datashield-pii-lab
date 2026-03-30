from __future__ import annotations

from pathlib import Path

from app.core.models import EntityType, SanitizationMode, SourceDocument
from app.detectors.regex_detector import detect_with_regex
from app.transformers.masker import mask_value
from app.transformers.redactor import redact_value
from app.transformers.sanitizer import apply_sanitization


def test_mask_value_email() -> None:
    masked = mask_value("mario.rossi@example.it", EntityType.EMAIL)
    assert masked == "m***o.r***i@example.it"


def test_mask_value_phone() -> None:
    masked = mask_value("+39 3331234567", EntityType.PHONE)
    assert masked == "+39 333****567"


def test_mask_value_person_name() -> None:
    masked = mask_value("Mario Rossi", EntityType.PERSON_NAME)
    assert masked == "M***o R***i"


def test_mask_value_ip_address() -> None:
    masked = mask_value("192.168.1.42", EntityType.IP_ADDRESS)
    assert masked == "192.***.***.42"


def test_redact_value() -> None:
    assert redact_value("foo", EntityType.IBAN) == "[REDACTED_IBAN]"


def test_apply_sanitization_replaces_values() -> None:
    content = [{
        "full_name": "Mario Rossi",
        "birth_date": "1985-06-14",
        "address": "Via Roma 10",
        "ip_address": "192.168.1.42",
        "email": "mario.rossi@example.it",
        "iban": "IT60X0542811101000000123456",
    }]
    source = SourceDocument(input_path=Path("sample.json"), input_format="json", content=content)
    detections = tuple(detect_with_regex(source))

    result = apply_sanitization(source, detections, SanitizationMode.MASK)

    sanitized_row = result.content[0]
    assert sanitized_row["full_name"] == "M***o R***i"
    assert sanitized_row["birth_date"] == "1**5-**-**"
    assert sanitized_row["address"] == "V*a R**a **"
    assert sanitized_row["ip_address"] == "192.***.***.42"
    assert sanitized_row["email"] == "m***o.r***i@example.it"
    assert sanitized_row["iban"].startswith("IT")
