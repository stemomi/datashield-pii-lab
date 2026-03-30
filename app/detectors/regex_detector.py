"""Regex and field-context detection for supported PII types."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Iterable

from ..core.models import DetectedEntity, EntityLocation, EntityType, SourceDocument
from . import custom_rules


@dataclass(frozen=True)
class RegexRule:
    """Encapsulate a regex rule and its entity type."""

    entity_type: EntityType
    pattern: re.Pattern[str]
    confidence: float = 0.85
    name: str = "regex"


@dataclass(frozen=True)
class ContextRule:
    """Encapsulate a field-aware rule for structured records."""

    entity_type: EntityType
    field_hints: tuple[str, ...]
    value_pattern: re.Pattern[str]
    confidence: float = 0.75
    name: str = "context"


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
BIRTH_DATE_PATTERN = re.compile(
    r"(?<!\d)(?:(?:0?[1-9]|[12]\d|3[01])[/-](?:0?[1-9]|1[0-2])[/-](?:19\d{2}|20\d{2})|"
    r"(?:19\d{2}|20\d{2})[/-](?:0?[1-9]|1[0-2])[/-](?:0?[1-9]|[12]\d|3[01]))(?!\d)"
)
IP_ADDRESS_PATTERN = re.compile(
    r"(?<!\d)(?:(?:25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)\.){3}(?:25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)(?!\d)"
)
PERSON_NAME_PATTERN = re.compile(
    r"^[A-ZÀ-ÖØ-Þ][A-Za-zÀ-ÖØ-öø-ÿ'`-]+(?:\s+[A-ZÀ-ÖØ-Þ][A-Za-zÀ-ÖØ-öø-ÿ'`-]+)+$"
)
ADDRESS_PATTERN = re.compile(
    r"(?i)^(?:via|viale|piazza|corso|largo|vicolo|piazzale|strada|street|road|avenue|boulevard|lane)\s+.+(?:\d|,).*$"
)
_FIELD_NAME_SANITIZER = re.compile(r"[^a-z0-9]+")

DEFAULT_RULES = (
    RegexRule(EntityType.EMAIL, EMAIL_PATTERN, confidence=0.9, name="email-regex"),
    RegexRule(EntityType.PHONE, PHONE_PATTERN, confidence=0.7, name="phone-regex"),
    RegexRule(EntityType.TAX_CODE, TAX_CODE_PATTERN, confidence=0.95, name="tax-code-regex"),
    RegexRule(EntityType.IBAN, IBAN_PATTERN, confidence=0.95, name="iban-regex"),
    RegexRule(EntityType.BIRTH_DATE, BIRTH_DATE_PATTERN, confidence=0.85, name="birth-date-regex"),
    RegexRule(EntityType.IP_ADDRESS, IP_ADDRESS_PATTERN, confidence=0.9, name="ip-address-regex"),
)

CONTEXT_RULES = (
    ContextRule(
        EntityType.PERSON_NAME,
        field_hints=("full_name", "person_name", "name", "nome", "first_name", "last_name", "contact_name"),
        value_pattern=PERSON_NAME_PATTERN,
        confidence=0.72,
        name="person-name-context",
    ),
    ContextRule(
        EntityType.ADDRESS,
        field_hints=("address", "street_address", "home_address", "billing_address", "shipping_address", "address_line", "indirizzo"),
        value_pattern=ADDRESS_PATTERN,
        confidence=0.78,
        name="address-context",
    ),
)


def detect_with_regex(source: SourceDocument) -> list[DetectedEntity]:
    """Detect candidate PII entities using regex and contextual rules."""
    detections: list[DetectedEntity] = []
    for rule in _iter_regex_rules():
        detections.extend(_apply_rule(source, rule))
    detections.extend(_detect_contextual_entities(source))
    return detections


def _iter_regex_rules() -> Iterable[RegexRule]:
    """Yield built-in rules followed by any project-local custom rules."""
    yield from DEFAULT_RULES
    yield from _build_custom_regex_rules()


def _build_custom_regex_rules() -> list[RegexRule]:
    """Build regex rules declared in app.detectors.custom_rules."""
    custom_regex_rules: list[RegexRule] = []

    for entity_name, raw_pattern in custom_rules.CUSTOM_ENTITY_RULES.items():
        entity_type = EntityType(entity_name)
        pattern = _compile_custom_pattern(entity_name, raw_pattern)
        custom_regex_rules.append(
            RegexRule(
                entity_type=entity_type,
                pattern=pattern,
                confidence=0.8,
                name=f"custom-{entity_type.value.lower()}-regex",
            )
        )

    return custom_regex_rules


def _compile_custom_pattern(entity_name: str, raw_pattern: custom_rules.CustomRulePattern) -> re.Pattern[str]:
    if isinstance(raw_pattern, re.Pattern):
        return raw_pattern
    try:
        return re.compile(raw_pattern)
    except re.error as exc:
        raise ValueError(f"Invalid custom regex rule for {entity_name}: {exc}") from exc


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


def _detect_contextual_entities(source: SourceDocument) -> list[DetectedEntity]:
    """Detect entities based on field names and structured-value patterns."""
    detections: list[DetectedEntity] = []

    if isinstance(source.content, list):
        for index, record in enumerate(source.content):
            detections.extend(_scan_contextual_value(record, record_index=index, field_path=()))
        return detections

    return _scan_contextual_value(source.content, record_index=None, field_path=())


def _scan_contextual_value(
    value: object,
    *,
    record_index: int | None,
    field_path: tuple[str | int, ...],
) -> list[DetectedEntity]:
    detections: list[DetectedEntity] = []

    if isinstance(value, dict):
        for key, item in value.items():
            detections.extend(
                _scan_contextual_value(item, record_index=record_index, field_path=(*field_path, key))
            )
        return detections

    if isinstance(value, list):
        for index, item in enumerate(value):
            detections.extend(
                _scan_contextual_value(item, record_index=record_index, field_path=(*field_path, index))
            )
        return detections

    return _scan_contextual_scalar(value, record_index=record_index, field_path=field_path)


def _scan_contextual_scalar(
    value: object,
    *,
    record_index: int | None,
    field_path: tuple[str | int, ...],
) -> list[DetectedEntity]:
    if value is None or not field_path or not isinstance(field_path[-1], str):
        return []

    text = str(value).strip()
    if not text:
        return []

    detections: list[DetectedEntity] = []
    for rule in CONTEXT_RULES:
        if not _field_matches(rule.field_hints, field_path[-1]):
            continue
        if not rule.value_pattern.fullmatch(text):
            continue
        detections.append(
            DetectedEntity(
                entity_type=rule.entity_type,
                value=text,
                location=EntityLocation(
                    field_path=field_path,
                    record_index=record_index,
                    char_start=0,
                    char_end=len(text),
                ),
                confidence=rule.confidence,
                detector_name=rule.name,
            )
        )
    return detections


def _field_matches(field_hints: tuple[str, ...], field_name: str) -> bool:
    normalized = _normalize_field_name(field_name)
    for hint in field_hints:
        if normalized == hint:
            return True
        if normalized.startswith(f"{hint}_") or normalized.endswith(f"_{hint}"):
            return True
    return False


def _normalize_field_name(field_name: str) -> str:
    lowered = field_name.strip().lower()
    return _FIELD_NAME_SANITIZER.sub("_", lowered).strip("_")


def iter_supported_entity_types() -> Iterable[str]:
    """Return the supported entity types for regex detection."""
    yielded: set[str] = set()
    for rule in _iter_regex_rules():
        if rule.entity_type.value not in yielded:
            yielded.add(rule.entity_type.value)
            yield rule.entity_type.value
    for rule in CONTEXT_RULES:
        if rule.entity_type.value not in yielded:
            yielded.add(rule.entity_type.value)
            yield rule.entity_type.value
