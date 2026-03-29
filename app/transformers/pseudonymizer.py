"""Deterministic pseudonymization utilities."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ..config import OUTPUTS_DIR
from ..core.models import EntityType


@dataclass
class PseudonymStore:
    """Persistent mapping store for deterministic pseudonyms."""

    path: Path = OUTPUTS_DIR / "pseudonym_map.json"

    def load(self) -> dict[str, Any]:
        if not self.path.exists():
            return {"counters": {}, "values": {}}
        return json.loads(self.path.read_text(encoding="utf-8"))

    def save(self, data: dict[str, Any]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(data, indent=2), encoding="utf-8")


class Pseudonymizer:
    """Create deterministic pseudonyms using a stored mapping."""

    def __init__(self, store: PseudonymStore | None = None) -> None:
        self.store = store or PseudonymStore()

    def pseudonymize(self, value: str, entity_type: EntityType | str) -> str:
        entity = EntityType(entity_type) if not isinstance(entity_type, EntityType) else entity_type
        data = self.store.load()
        values = data.setdefault("values", {})
        counters = data.setdefault("counters", {})

        key = f"{entity.value}::{value}"
        existing = values.get(key)
        if existing:
            return existing

        count = int(counters.get(entity.value, 0)) + 1
        counters[entity.value] = count
        pseudonym = f"{entity.value}_{count:03d}"
        values[key] = pseudonym

        self.store.save(data)
        return pseudonym
