"""JSON ingestion utilities."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


JsonRecord = dict[str, Any]


def load_json(source_path: Path) -> JsonRecord | list[JsonRecord]:
    """Load JSON data from disk and normalize it for scanning."""
    if not source_path.exists():
        raise FileNotFoundError(f"JSON file not found: {source_path}")
    if source_path.suffix.lower() != ".json":
        raise ValueError(f"Expected a .json file, got: {source_path}")

    with source_path.open(mode="r", encoding="utf-8-sig") as handle:
        payload = json.load(handle)

    return _normalize_json(payload)


def _normalize_json(payload: Any) -> JsonRecord | list[JsonRecord]:
    """Normalize JSON payloads into dicts or list-of-dicts for scanning."""
    if isinstance(payload, list):
        normalized: list[JsonRecord] = []
        for item in payload:
            if isinstance(item, dict):
                normalized.append(item)
            else:
                normalized.append({"value": item})
        return normalized
    if isinstance(payload, dict):
        # Heuristic: if a top-level "records" list exists, prefer it.
        records = payload.get("records")
        if isinstance(records, list):
            return _normalize_json(records)
        return payload
    return {"value": payload}
