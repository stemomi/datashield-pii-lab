"""JSON ingestion scaffolding."""

from __future__ import annotations

from pathlib import Path


def load_json(_: Path) -> dict[str, object] | list[dict[str, object]]:
    """Load JSON data from disk.

    The concrete implementation is planned for phase 3.
    """
    raise NotImplementedError("JSON ingestion will be implemented in phase 3.")
