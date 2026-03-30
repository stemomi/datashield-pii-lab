from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

from app.core.models import EntityType, SourceDocument
from app.detectors.presidio_detector import detect_with_presidio


class _FakeAnalyzerEngine:
    def analyze(self, text: str, entities: list[str], language: str):
        assert language == "en"
        assert entities == ["EMAIL_ADDRESS"]
        start = text.index("mario.rossi@example.it")
        end = start + len("mario.rossi@example.it")
        return [
            SimpleNamespace(
                entity_type="EMAIL_ADDRESS",
                start=start,
                end=end,
                score=0.99,
            )
        ]


def test_presidio_detector_maps_results_without_real_engine(monkeypatch) -> None:
    monkeypatch.setattr(
        "app.detectors.presidio_detector.AnalyzerEngine",
        _FakeAnalyzerEngine,
    )

    source = SourceDocument(
        input_path=Path("sample.txt"),
        input_format="txt",
        content="My email is mario.rossi@example.it",
    )

    detections = detect_with_presidio(source, entities=["EMAIL_ADDRESS"])

    assert len(detections) == 1
    detection = detections[0]
    assert detection.entity_type is EntityType.EMAIL
    assert detection.value == "mario.rossi@example.it"
    assert detection.detector_name == "presidio"
    assert detection.confidence == 0.99
    assert detection.location.char_start is not None
    assert detection.location.char_end is not None
