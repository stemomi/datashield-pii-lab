"""PDF ingestion utilities."""

from __future__ import annotations

from pathlib import Path

try:
    from pypdf import PdfReader
except ImportError as exc:  # pragma: no cover - handled by runtime import error
    raise ImportError(
        "pypdf is required for PDF ingestion. Install it with 'pip install pypdf'."
    ) from exc


def load_pdf(source_path: Path) -> str:
    """Load text content from a PDF file."""
    if not source_path.exists():
        raise FileNotFoundError(f"PDF file not found: {source_path}")
    if source_path.suffix.lower() != ".pdf":
        raise ValueError(f"Expected a .pdf file, got: {source_path}")

    reader = PdfReader(str(source_path))
    chunks: list[str] = []
    for page in reader.pages:
        text = page.extract_text() or ""
        if text:
            chunks.append(text)
    return "\n".join(chunks).strip()
