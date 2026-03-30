from __future__ import annotations

from pathlib import Path

from app.core.models import EntityType, SourceDocument
from app.detectors import custom_rules
from app.detectors.regex_detector import detect_with_regex


def test_regex_detector_finds_supported_entities() -> None:
    content = {
        "full_name": "Mario Rossi",
        "birth_date": "1985-06-14",
        "address": "Via Roma 10",
        "ip_address": "192.168.1.42",
        "email": "mario.rossi@example.it",
        "phone": "+39 3331234567",
        "tax_code": "RSSMRA85M01H501Z",
        "iban": "IT60X0542811101000000123456",
    }
    source = SourceDocument(input_path=Path("sample.json"), input_format="json", content=content)

    detections = detect_with_regex(source)
    types = {item.entity_type for item in detections}

    assert EntityType.PERSON_NAME in types
    assert EntityType.BIRTH_DATE in types
    assert EntityType.ADDRESS in types
    assert EntityType.IP_ADDRESS in types
    assert EntityType.EMAIL in types
    assert EntityType.PHONE in types
    assert EntityType.TAX_CODE in types
    assert EntityType.IBAN in types

    person_name = next(item for item in detections if item.entity_type is EntityType.PERSON_NAME)
    address = next(item for item in detections if item.entity_type is EntityType.ADDRESS)
    assert person_name.detector_name == "person-name-context"
    assert address.detector_name == "address-context"

    first = detections[0]
    assert first.location.char_start is not None
    assert first.location.char_end is not None
    assert first.confidence > 0


def test_regex_detector_uses_custom_rules(monkeypatch) -> None:
    monkeypatch.setattr(
        custom_rules,
        "CUSTOM_ENTITY_RULES",
        {"PERSON_NAME": r"OPERATORE\s+ALFA"},
    )
    source = SourceDocument(
        input_path=Path("sample.json"),
        input_format="json",
        content={"notes": "Alias OPERATORE ALFA per test locale"},
    )

    detections = detect_with_regex(source)

    custom_detection = next(item for item in detections if item.detector_name == "custom-person_name-regex")
    assert custom_detection.entity_type is EntityType.PERSON_NAME
    assert custom_detection.value == "OPERATORE ALFA"
