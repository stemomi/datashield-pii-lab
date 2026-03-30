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
    if entity is EntityType.IP_ADDRESS:
        return _mask_ip_address(value)
    if entity in (EntityType.PERSON_NAME, EntityType.ADDRESS, EntityType.BIRTH_DATE):
        return _mask_tokenized_text(value)
    if entity in (EntityType.TAX_CODE, EntityType.IBAN):
        return _mask_middle(value, keep_start=2, keep_end=2)
    return _mask_middle(value, keep_start=1, keep_end=1)


def _mask_email(value: str) -> str:
    if "@" not in value:
        return _mask_middle(value, keep_start=1, keep_end=1)

    local, domain = value.split("@", 1)
    masked_local = _mask_tokenized_text(local)
    return f"{masked_local}@{domain}"


def _mask_phone(value: str) -> str:
    digits = [index for index, char in enumerate(value) if char.isdigit()]
    total_digits = len(digits)
    if total_digits <= 4:
        return _mask_middle(value, keep_start=1, keep_end=1)

    keep_start_digits = 5 if total_digits > 8 else max(1, total_digits - 3)
    keep_end_digits = 3
    keep_indices = set(digits[:keep_start_digits] + digits[-keep_end_digits:])

    masked_chars = [
        char if (not char.isdigit() or index in keep_indices) else "*"
        for index, char in enumerate(value)
    ]
    return "".join(masked_chars)


def _mask_ip_address(value: str) -> str:
    octets = value.split(".")
    if len(octets) != 4 or not all(part.isdigit() for part in octets):
        return _mask_tokenized_text(value)
    return f"{octets[0]}.***.***.{octets[-1]}"


def _mask_tokenized_text(value: str) -> str:
    parts: list[str] = []
    token = ""

    for char in value:
        if char.isalnum():
            token += char
            continue
        if token:
            parts.append(_mask_middle(token, keep_start=1, keep_end=1))
            token = ""
        parts.append(char)

    if token:
        parts.append(_mask_middle(token, keep_start=1, keep_end=1))

    return "".join(parts)


def _mask_middle(value: str, *, keep_start: int, keep_end: int) -> str:
    if value is None:
        return ""
    text = str(value)
    if len(text) <= keep_start + keep_end:
        return "*" * len(text)
    return f"{text[:keep_start]}{'*' * (len(text) - keep_start - keep_end)}{text[-keep_end:]}"
