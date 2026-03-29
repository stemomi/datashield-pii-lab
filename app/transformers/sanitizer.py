"""Sanitization engine for masking and redaction."""

from __future__ import annotations

from typing import Iterable

from ..core.models import (
    AppliedTransformation,
    DetectedEntity,
    EntityLocation,
    PipelineRequest,
    SanitizationMode,
    SourceDocument,
    TransformResult,
)
from ..core.utils import clone_structured_data
from .masker import mask_value
from .redactor import redact_value


def apply_sanitization(
    source: SourceDocument,
    detections: tuple[DetectedEntity, ...],
    sanitization_mode: SanitizationMode,
) -> TransformResult:
    """Apply the requested sanitization mode to the detected entities."""
    content = clone_structured_data(source.content)
    applied: list[AppliedTransformation] = []

    for detection in detections:
        sanitized = _sanitize_value(detection.value, detection.entity_type, sanitization_mode)
        content = _apply_to_content(content, detection.location, detection.value, sanitized)
        applied.append(
            AppliedTransformation(
                entity=detection,
                mode=sanitization_mode,
                sanitized_value=sanitized,
            )
        )

    return TransformResult(content=content, applied_transformations=applied)


def _sanitize_value(value: str, entity_type: object, mode: SanitizationMode) -> str:
    if mode is SanitizationMode.REDACT:
        return redact_value(value, entity_type)
    return mask_value(value, entity_type)


def _apply_to_content(
    content: object,
    location: EntityLocation,
    original_value: str,
    sanitized_value: str,
) -> object:
    """Apply a sanitized value at the requested field path."""
    target = content
    if location.record_index is not None:
        if isinstance(content, list) and 0 <= location.record_index < len(content):
            target = content[location.record_index]
        else:
            return content

    if not location.field_path:
        if isinstance(target, str):
            return target.replace(original_value, sanitized_value)
        return content

    if isinstance(target, str) and location.field_path == ("value",):
        return target.replace(original_value, sanitized_value)

    parent, key = _resolve_parent(target, location.field_path)
    if parent is None:
        return content

    if isinstance(parent, dict) and isinstance(key, str):
        parent[key] = _sanitize_field(parent.get(key), original_value, sanitized_value)
    elif isinstance(parent, list) and isinstance(key, int) and 0 <= key < len(parent):
        parent[key] = _sanitize_field(parent[key], original_value, sanitized_value)

    return content


def _resolve_parent(content: object, field_path: tuple[str | int, ...]) -> tuple[object | None, str | int | None]:
    """Navigate to the parent container for the given field path."""
    current = content
    for part in field_path[:-1]:
        if isinstance(current, dict) and isinstance(part, str):
            current = current.get(part)
        elif isinstance(current, list) and isinstance(part, int) and 0 <= part < len(current):
            current = current[part]
        else:
            return None, None
    return current, field_path[-1]


def _sanitize_field(value: object, original_value: str, sanitized_value: str) -> object:
    """Replace occurrences inside a field while preserving structure when possible."""
    if value is None:
        return sanitized_value
    if isinstance(value, str):
        return value.replace(original_value, sanitized_value)
    if isinstance(value, (int, float, bool)):
        return sanitized_value
    return sanitized_value


def iter_sanitization_modes() -> Iterable[str]:
    """Return the supported sanitization modes."""
    return (mode.value for mode in SanitizationMode)
