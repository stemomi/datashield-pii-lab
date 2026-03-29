from __future__ import annotations

from pathlib import Path

import pytest

from app.core.models import SourceDocument
from app.detectors.presidio_detector import detect_with_presidio


@pytest.mark.filterwarnings("ignore::UserWarning")
def test_presidio_detector_optional() -> None:
    source = SourceDocument(
        input_path=Path("sample.txt"),
        input_format="txt",
        content="My email is mario.rossi@example.it",
    )

    try:
        detections = detect_with_presidio(source, entities=["EMAIL_ADDRESS"])
    except Exception as exc:  # noqa: BLE001 - optional dependency may fail in env
        pytest.skip(f"Presidio not available: {exc}")

    assert detections
