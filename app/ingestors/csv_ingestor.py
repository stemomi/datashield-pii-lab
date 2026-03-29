"""CSV ingestion scaffolding."""

from __future__ import annotations

from pathlib import Path


def load_csv(_: Path) -> list[dict[str, str]]:
    """Load CSV data from disk.

    The concrete implementation is planned for phase 2.
    """
    raise NotImplementedError("CSV ingestion will be implemented in phase 2.")
