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


def detect_with_presidio(
    source: SourceDocument,
    entities: Iterable[str] | None = None,
) -> list[DetectedEntity]:
    """Detect entities using Presidio Analyzer."""
    analyzer = AnalyzerEngine()
    targets = list(entities) if entities else [entity.value for entity in EntityType]

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
    if name in {"EMAIL_ADDRESS", "EMAIL"}:
        return EntityType.EMAIL
    if name in {"PHONE_NUMBER", "PHONE"}:
        return EntityType.PHONE
    if name == "IBAN_CODE":
        return EntityType.IBAN
    if name == "IT_FISCAL_CODE":
        return EntityType.TAX_CODE
    return EntityType(name)
