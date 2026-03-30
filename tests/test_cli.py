from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from app.cli import run


def _write_cli_config(tmp_path: Path) -> Path:
    config_path = tmp_path / "config.json"
    config_path.write_text(json.dumps({"output_dir": str(tmp_path)}), encoding="utf-8")
    return config_path


def test_cli_sanitize_creates_sanitized_output_and_report(tmp_path: Path, capsys) -> None:
    input_path = tmp_path / "customers.csv"
    input_path.write_text(
        "full_name,birth_date,address,ip_address,email,phone\n"
        "Mario Rossi,1985-06-14,Via Roma 10,192.168.1.42,mario.rossi@example.it,+39 3331234567\n",
        encoding="utf-8",
    )
    config_path = _write_cli_config(tmp_path)

    exit_code = run(["--config", str(config_path), "sanitize", str(input_path), "--mode", "mask"])

    assert exit_code == 0
    sanitized_path = tmp_path / "customers_mask_sanitized.csv"
    report_path = tmp_path / "customers_mask_report.json"

    assert sanitized_path.exists()
    assert report_path.exists()
    assert "Sanitization completed." in capsys.readouterr().out

    sanitized_content = sanitized_path.read_text(encoding="utf-8")
    assert "M***o R***i" in sanitized_content
    assert "1**5-**-**" in sanitized_content
    assert "V*a R**a **" in sanitized_content
    assert "192.***.***.42" in sanitized_content
    assert "m***o.r***i@example.it" in sanitized_content
    assert "+39 333****567" in sanitized_content

    report = json.loads(report_path.read_text(encoding="utf-8"))
    assert report["output_file"] == str(sanitized_path)
    assert report["sanitized_output_generated"] is True
    assert report["planned_outputs"]["sanitized_file"] == str(sanitized_path)
    assert report["entity_counts"]["PERSON_NAME"] == 1
    assert report["entity_counts"]["BIRTH_DATE"] == 1
    assert report["entity_counts"]["ADDRESS"] == 1
    assert report["entity_counts"]["IP_ADDRESS"] == 1


def test_cli_report_does_not_claim_sanitized_output(tmp_path: Path, capsys) -> None:
    input_path = tmp_path / "customers.csv"
    input_path.write_text(
        "full_name,email\n"
        "Mario Rossi,mario.rossi@example.it\n",
        encoding="utf-8",
    )
    config_path = _write_cli_config(tmp_path)

    exit_code = run(["--config", str(config_path), "report", str(input_path), "--mode", "mask"])

    assert exit_code == 0
    report_path = tmp_path / "customers_mask_report.json"

    assert report_path.exists()
    assert "Report generated." in capsys.readouterr().out

    report = json.loads(report_path.read_text(encoding="utf-8"))
    assert report["output_file"] is None
    assert report["sanitized_output_generated"] is False
    assert report["planned_outputs"]["sanitized_file"] is None
    assert report["transformations"] == []
    assert report["entity_counts"]["PERSON_NAME"] == 1
    assert report["entity_counts"]["EMAIL"] == 1
    assert not (tmp_path / "customers_mask_sanitized.csv").exists()


def test_cli_db_reports_missing_table_cleanly(tmp_path: Path, capsys) -> None:
    db_path = tmp_path / "empty.db"
    sqlite3.connect(db_path).close()

    exit_code = run([
        "db",
        "--url",
        f"sqlite:///{db_path}",
        "--query",
        "select * from customers",
    ])

    assert exit_code == 1
    output = capsys.readouterr().out
    assert "Database scan failed:" in output
    assert "no such table: customers" in output
    assert "currently has no tables" in output


def test_cli_db_generates_report_for_sqlite_table(tmp_path: Path, capsys) -> None:
    db_path = tmp_path / "demo.db"
    conn = sqlite3.connect(db_path)
    try:
        conn.execute(
            "create table customers (full_name text, email text, ip_address text)"
        )
        conn.execute(
            "insert into customers (full_name, email, ip_address) values (?, ?, ?)",
            ("Mario Rossi", "mario.rossi@example.it", "192.168.1.42"),
        )
        conn.commit()
    finally:
        conn.close()

    config_path = _write_cli_config(tmp_path)
    exit_code = run([
        "--config",
        str(config_path),
        "db",
        "--url",
        f"sqlite:///{db_path}",
        "--query",
        "select * from customers",
    ])

    assert exit_code == 0
    report_path = tmp_path / "demo_mask_report.json"
    assert report_path.exists()
    output = capsys.readouterr().out
    assert "Database scan completed." in output

    report = json.loads(report_path.read_text(encoding="utf-8"))
    assert report["input_file"] == "demo.db"
    assert report["entity_counts"]["PERSON_NAME"] == 1
    assert report["entity_counts"]["EMAIL"] == 1
    assert report["entity_counts"]["IP_ADDRESS"] == 1
    assert report["output_file"] is None
