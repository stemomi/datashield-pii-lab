from __future__ import annotations

import sqlite3
from pathlib import Path

from app.ingestors.db_ingestor import load_db


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
