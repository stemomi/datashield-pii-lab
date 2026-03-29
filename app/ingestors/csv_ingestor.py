"""CSV ingestion utilities."""

from __future__ import annotations

import csv
from pathlib import Path


def load_csv(source_path: Path) -> list[dict[str, str]]:
    """Load CSV data from disk and normalize rows for scanning."""
    if not source_path.exists():
        raise FileNotFoundError(f"CSV file not found: {source_path}")
    if source_path.suffix.lower() != ".csv":
        raise ValueError(f"Expected a .csv file, got: {source_path}")

    with source_path.open(mode="r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        rows: list[dict[str, str]] = []
        for row in reader:
            # DictReader can emit None keys for malformed rows; ignore them.
            normalized = {key: (value or "") for key, value in row.items() if key is not None}
            rows.append(normalized)
    return rows
