"""SQL dump ingestion utilities."""

from __future__ import annotations

from pathlib import Path


def load_sql(source_path: Path) -> str:
    """Load SQL dump content from disk for scanning."""
    if not source_path.exists():
        raise FileNotFoundError(f"SQL file not found: {source_path}")
    if source_path.suffix.lower() != ".sql":
        raise ValueError(f"Expected a .sql file, got: {source_path}")

    return source_path.read_text(encoding="utf-8")
