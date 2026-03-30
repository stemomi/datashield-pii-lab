"""Database ingestion utilities."""

from __future__ import annotations

from typing import Any

try:
    from sqlalchemy import create_engine, inspect, text
    from sqlalchemy.exc import SQLAlchemyError
except ImportError as exc:  # pragma: no cover
    raise ImportError(
        "sqlalchemy is required for database ingestion. Install it with 'pip install sqlalchemy'."
    ) from exc


class DatabaseQueryError(RuntimeError):
    """Raised when a database query cannot be executed successfully."""


def load_db(query: str, connection_url: str) -> list[dict[str, Any]]:
    """Load rows from a database query and return them as dicts."""
    engine = create_engine(connection_url)
    rows: list[dict[str, Any]] = []

    try:
        with engine.connect() as connection:
            result = connection.execute(text(query))
            columns = result.keys()
            for row in result.fetchall():
                rows.append({column: value for column, value in zip(columns, row)})
    except SQLAlchemyError as exc:
        raise DatabaseQueryError(_build_query_error_message(connection_url, exc, engine)) from exc

    return rows


def _build_query_error_message(connection_url: str, exc: Exception, engine: Any) -> str:
    message = str(exc)
    if not connection_url.startswith("sqlite:///"):
        return message

    lowered = message.lower()
    tables = inspect(engine).get_table_names()
    if "no such table" in lowered:
        if tables:
            return f"{message}. Available tables: {', '.join(tables)}"
        return f"{message}. The SQLite database currently has no tables."

    return message
