"""Regex-based detection for MVP PII types."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Iterable

from ..core.models import DetectedEntity, EntityLocation, EntityType, SourceDocument


@dataclass(frozen=True)
class RegexRule:
    """Encapsulate a regex rule and its entity type."""

    entity_type: EntityType
    pattern: re.Pattern[str]
    confidence: float = 0.85
    name: str = "regex"


EMAIL_PATTERN = re.compile(
    r"(?i)(?<![\w.-])[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}(?![\w.-])"
)
PHONE_PATTERN = re.compile(
    r"(?x)(?<!\d)(?:\+\d{1,3}\s?)?(?:\(\d{2,4}\)\s?)?"
    r"\d{2,4}[\s.-]?\d{3,4}[\s.-]?\d{3,4}(?!\d)"
)
TAX_CODE_PATTERN = re.compile(
    r"(?i)(?<![A-Z0-9])"
    r"[A-Z]{6}\d{2}[A-Z]\d{2}[A-Z]\d{3}[A-Z](?![A-Z0-9])"
)
IBAN_PATTERN = re.compile(
    r"(?i)(?<![A-Z0-9])IT\d{2}[A-Z]\d{10}[A-Z0-9]{12}(?![A-Z0-9])"
)

DEFAULT_RULES = (
    RegexRule(EntityType.EMAIL, EMAIL_PATTERN, confidence=0.9, name="email-regex"),
    RegexRule(EntityType.PHONE, PHONE_PATTERN, confidence=0.7, name="phone-regex"),
    RegexRule(EntityType.TAX_CODE, TAX_CODE_PATTERN, confidence=0.95, name="tax-code-regex"),
    RegexRule(EntityType.IBAN, IBAN_PATTERN, confidence=0.95, name="iban-regex"),
)


def detect_with_regex(source: SourceDocument) -> list[DetectedEntity]:
    """Detect candidate PII entities using regex rules."""
    detections: list[DetectedEntity] = []
    for rule in DEFAULT_RULES:
        detections.extend(_apply_rule(source, rule))
    return detections


def _apply_rule(source: SourceDocument, rule: RegexRule) -> list[DetectedEntity]:
    """Apply a regex rule to a source document."""
    detections: list[DetectedEntity] = []

    if isinstance(source.content, list):
        for index, record in enumerate(source.content):
            if isinstance(record, dict):
                detections.extend(
                    _scan_mapping(record, rule, record_index=index, field_prefix=())
                )
            else:
                detections.extend(
                    _scan_scalar(record, rule, record_index=index, field_path=("value",))
                )
        return detections

    if isinstance(source.content, dict):
        detections.extend(_scan_mapping(source.content, rule, record_index=None, field_prefix=()))
        return detections

    detections.extend(
        _scan_scalar(source.content, rule, record_index=None, field_path=())
    )
    return detections


def _scan_mapping(
    mapping: dict[str, object],
    rule: RegexRule,
    *,
    record_index: int | None,
    field_prefix: tuple[str | int, ...],
) -> list[DetectedEntity]:
    detections: list[DetectedEntity] = []
    for key, value in mapping.items():
        field_path = (*field_prefix, key)
        detections.extend(
            _scan_value(value, rule, record_index=record_index, field_path=field_path)
        )
    return detections


def _scan_value(
    value: object,
    rule: RegexRule,
    *,
    record_index: int | None,
    field_path: tuple[str | int, ...],
) -> list[DetectedEntity]:
    detections: list[DetectedEntity] = []

    if isinstance(value, dict):
        detections.extend(_scan_mapping(value, rule, record_index=record_index, field_prefix=field_path))
        return detections

    if isinstance(value, list):
        for idx, item in enumerate(value):
            detections.extend(
                _scan_value(item, rule, record_index=record_index, field_path=(*field_path, idx))
            )
        return detections

    detections.extend(
        _scan_scalar(value, rule, record_index=record_index, field_path=field_path)
    )
    return detections


def _scan_scalar(
    value: object,
    rule: RegexRule,
    *,
    record_index: int | None,
    field_path: tuple[str | int, ...],
) -> list[DetectedEntity]:
    if value is None:
        return []
    if isinstance(value, (int, float, bool)):
        text = str(value)
    else:
        text = str(value)

    detections: list[DetectedEntity] = []
    for match in rule.pattern.finditer(text):
        detection = DetectedEntity(
            entity_type=rule.entity_type,
            value=match.group(0),
            location=EntityLocation(
                field_path=field_path,
                record_index=record_index,
                char_start=match.start(),
                char_end=match.end(),
            ),
            confidence=rule.confidence,
            detector_name=rule.name,
        )
        detections.append(detection)
    return detections


def iter_supported_entity_types() -> Iterable[str]:
    """Return the supported entity types for regex detection."""
    return (rule.entity_type.value for rule in DEFAULT_RULES)
