from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from app.ingestors.db_ingestor import DatabaseQueryError, load_db


def test_load_db_with_sqlite(tmp_path: Path) -> None:
    db_path = tmp_path / "test.db"
    conn = sqlite3.connect(db_path)
    try:
        conn.execute("create table customers (email text)")
        conn.execute("insert into customers (email) values ('mario.rossi@example.it')")
        conn.commit()
    finally:
        conn.close()

    rows = load_db("select email from customers", f"sqlite:///{db_path}")

    assert rows == [{"email": "mario.rossi@example.it"}]


def test_load_db_reports_missing_sqlite_table(tmp_path: Path) -> None:
    db_path = tmp_path / "empty.db"
    sqlite3.connect(db_path).close()

    with pytest.raises(DatabaseQueryError) as excinfo:
        load_db("select * from customers", f"sqlite:///{db_path}")

    assert "no such table: customers" in str(excinfo.value)
    assert "currently has no tables" in str(excinfo.value)
