"""Masking transformer utilities."""

from __future__ import annotations

from ..core.models import EntityType


def mask_value(value: str, entity_type: EntityType | str) -> str:
    """Mask a sensitive value according to its entity type."""
    entity = EntityType(entity_type) if not isinstance(entity_type, EntityType) else entity_type

    if entity is EntityType.EMAIL:
        return _mask_email(value)
    if entity is EntityType.PHONE:
        return _mask_phone(value)
    if entity in (EntityType.TAX_CODE, EntityType.IBAN):
        return _mask_middle(value, keep_start=2, keep_end=2)
    return _mask_middle(value, keep_start=1, keep_end=1)


def _mask_email(value: str) -> str:
    if "@" not in value:
        return _mask_middle(value, keep_start=1, keep_end=1)
    local, domain = value.split("@", 1)
    masked_local = _mask_middle(local, keep_start=1, keep_end=1)
    return f"{masked_local}@{domain}"


def _mask_phone(value: str) -> str:
    # Preserve the general shape while hiding the middle section.
    return _mask_middle(value, keep_start=4, keep_end=3)


def _mask_middle(value: str, *, keep_start: int, keep_end: int) -> str:
    if value is None:
        return ""
    text = str(value)
    if len(text) <= keep_start + keep_end:
        return "*" * len(text)
    return f"{text[:keep_start]}{'*' * (len(text) - keep_start - keep_end)}{text[-keep_end:]}"
