"""Database ingestion utilities."""

from __future__ import annotations

from collections.abc import Iterable
from typing import Any

try:
    from sqlalchemy import create_engine, text
except ImportError as exc:  # pragma: no cover
    raise ImportError(
        "sqlalchemy is required for database ingestion. Install it with 'pip install sqlalchemy'."
    ) from exc


def load_db(query: str, connection_url: str) -> list[dict[str, Any]]:
    """Load rows from a database query and return them as dicts."""
    engine = create_engine(connection_url)
    rows: list[dict[str, Any]] = []

    with engine.connect() as connection:
        result = connection.execute(text(query))
        columns = result.keys()
        for row in result.fetchall():
            rows.append({column: value for column, value in zip(columns, row)})

    return rows
