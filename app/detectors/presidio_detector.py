"""Presidio-based detector utilities."""

from __future__ import annotations

from typing import Iterable

try:
    from presidio_analyzer import AnalyzerEngine
except ImportError as exc:  # pragma: no cover
    raise ImportError(
        "presidio-analyzer is required for Presidio detection. Install it with 'pip install presidio-analyzer'."
    ) from exc

from ..core.models import DetectedEntity, EntityLocation, EntityType, SourceDocument

_INTERNAL_TO_PRESIDIO = {
    EntityType.EMAIL: "EMAIL_ADDRESS",
    EntityType.PHONE: "PHONE_NUMBER",
    EntityType.TAX_CODE: "IT_FISCAL_CODE",
    EntityType.IBAN: "IBAN_CODE",
    EntityType.BIRTH_DATE: "DATE_TIME",
    EntityType.ADDRESS: "LOCATION",
    EntityType.IP_ADDRESS: "IP_ADDRESS",
    EntityType.PERSON_NAME: "PERSON",
}

_PRESIDIO_TO_INTERNAL = {
    "EMAIL_ADDRESS": EntityType.EMAIL,
    "EMAIL": EntityType.EMAIL,
    "PHONE_NUMBER": EntityType.PHONE,
    "PHONE": EntityType.PHONE,
    "IT_FISCAL_CODE": EntityType.TAX_CODE,
    "IBAN_CODE": EntityType.IBAN,
    "DATE_TIME": EntityType.BIRTH_DATE,
    "BIRTH_DATE": EntityType.BIRTH_DATE,
    "LOCATION": EntityType.ADDRESS,
    "ADDRESS": EntityType.ADDRESS,
    "IP_ADDRESS": EntityType.IP_ADDRESS,
    "PERSON": EntityType.PERSON_NAME,
    "PERSON_NAME": EntityType.PERSON_NAME,
}


def detect_with_presidio(
    source: SourceDocument,
    entities: Iterable[str] | None = None,
) -> list[DetectedEntity]:
    """Detect entities using Presidio Analyzer."""
    analyzer = AnalyzerEngine()
    targets = list(entities) if entities else list(_INTERNAL_TO_PRESIDIO.values())

    text = _flatten_source(source)
    results = analyzer.analyze(text=text, entities=targets, language="en")

    detections: list[DetectedEntity] = []
    for item in results:
        detections.append(
            DetectedEntity(
                entity_type=_normalize_entity_type(item.entity_type),
                value=text[item.start : item.end],
                location=EntityLocation(field_path=(), record_index=None, char_start=item.start, char_end=item.end),
                confidence=item.score,
                detector_name="presidio",
            )
        )
    return detections


def _flatten_source(source: SourceDocument) -> str:
    if isinstance(source.content, list):
        return "\n".join(str(item) for item in source.content)
    if isinstance(source.content, dict):
        return "\n".join(str(value) for value in source.content.values())
    return str(source.content)


def _normalize_entity_type(name: str) -> EntityType:
    entity = _PRESIDIO_TO_INTERNAL.get(name)
    if entity is not None:
        return entity
    return EntityType(name)
