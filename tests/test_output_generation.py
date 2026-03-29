from __future__ import annotations

import json
from pathlib import Path

from app.cli import _write_json, _write_report, _write_sanitized_output


def test_write_json_output(tmp_path: Path) -> None:
    output_path = tmp_path / "payload.json"
    payload = {"status": "ok"}

    _write_json(payload, output_path)

    assert json.loads(output_path.read_text(encoding="utf-8")) == payload


def test_write_csv_output(tmp_path: Path) -> None:
    output_path = tmp_path / "payload.csv"
    content = [{"email": "a@example.it", "phone": "123"}]

    _write_sanitized_output("csv", content, output_path)

    rows = output_path.read_text(encoding="utf-8").splitlines()
    assert rows[0] == "email,phone"
    assert rows[1] == "a@example.it,123"


def test_write_report_output(tmp_path: Path) -> None:
    output_path = tmp_path / "report.json"
    report = {"entities_found": 2}

    _write_report(report, output_path)

    assert json.loads(output_path.read_text(encoding="utf-8")) == report
