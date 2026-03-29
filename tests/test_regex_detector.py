from __future__ import annotations

from pathlib import Path

from app.core.models import EntityType, SourceDocument
from app.detectors.regex_detector import detect_with_regex


def test_regex_detector_finds_entities() -> None:
    content = {
        "email": "mario.rossi@example.it",
        "phone": "+39 3331234567",
        "tax_code": "RSSMRA85M01H501Z",
        "iban": "IT60X0542811101000000123456",
    }
    source = SourceDocument(input_path=Path("sample.json"), input_format="json", content=content)

    detections = detect_with_regex(source)
    types = {item.entity_type for item in detections}

    assert EntityType.EMAIL in types
    assert EntityType.PHONE in types
    assert EntityType.TAX_CODE in types
    assert EntityType.IBAN in types

    first = detections[0]
    assert first.location.char_start is not None
    assert first.location.char_end is not None
    assert first.confidence > 0
