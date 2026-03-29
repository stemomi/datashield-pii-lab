"""Redaction transformer utilities."""

from __future__ import annotations

from ..core.models import EntityType


def redact_value(_: str, entity_type: EntityType | str) -> str:
    """Redact a sensitive value according to its entity type."""
    entity = EntityType(entity_type) if not isinstance(entity_type, EntityType) else entity_type
    return f"[REDACTED_{entity.value}]"
