from __future__ import annotations

import json
from pathlib import Path

from app.ingestors.csv_ingestor import load_csv
from app.ingestors.json_ingestor import load_json
from app.ingestors.txt_ingestor import load_txt
from app.ingestors.pdf_ingestor import load_pdf


def test_load_csv_reads_rows(tmp_path: Path) -> None:
    csv_path = tmp_path / "sample.csv"
    csv_path.write_text(
        "name,email\nMario,mario.rossi@example.it\nAnna,anna@example.it\n",
        encoding="utf-8",
    )

    rows = load_csv(csv_path)

    assert rows == [
        {"name": "Mario", "email": "mario.rossi@example.it"},
        {"name": "Anna", "email": "anna@example.it"},
    ]


def test_load_json_list_normalization(tmp_path: Path) -> None:
    payload = [
        {"email": "mario@example.it"},
        "just a string",
        42,
    ]
    json_path = tmp_path / "sample.json"
    json_path.write_text(json.dumps(payload), encoding="utf-8")

    data = load_json(json_path)

    assert data == [
        {"email": "mario@example.it"},
        {"value": "just a string"},
        {"value": 42},
    ]


def test_load_json_records_key(tmp_path: Path) -> None:
    payload = {"records": [{"email": "anna@example.it"}]}
    json_path = tmp_path / "records.json"
    json_path.write_text(json.dumps(payload), encoding="utf-8")

    data = load_json(json_path)

    assert data == [{"email": "anna@example.it"}]


def test_load_txt_reads_text(tmp_path: Path) -> None:
    txt_path = tmp_path / "sample.txt"
    txt_path.write_text("mario.rossi@example.it", encoding="utf-8")

    text = load_txt(txt_path)

    assert text == "mario.rossi@example.it"


def test_load_pdf_reads_text() -> None:
    pdf_path = Path("samples/sample_text.pdf")
    text = load_pdf(pdf_path)

    assert "mario.rossi@example.it" in text
