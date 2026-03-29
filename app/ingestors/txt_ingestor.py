"""TXT ingestion utilities."""

from __future__ import annotations

from pathlib import Path


def load_txt(source_path: Path) -> str:
    """Load plain-text data from disk."""
    if not source_path.exists():
        raise FileNotFoundError(f"TXT file not found: {source_path}")
    if source_path.suffix.lower() != ".txt":
        raise ValueError(f"Expected a .txt file, got: {source_path}")

    return source_path.read_text(encoding="utf-8")
