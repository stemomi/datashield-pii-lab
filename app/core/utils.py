"""Shared utility helpers for file handling and output naming."""

from __future__ import annotations

from copy import deepcopy
from pathlib import Path

from ..config import (
    DEFAULT_REPORT_FORMAT,
    DEFAULT_REPORT_SUFFIX,
    DEFAULT_SANITIZED_SUFFIX,
    OUTPUTS_DIR,
    SUPPORTED_INPUT_FORMATS,
)
from .models import FieldPath, StructuredData


def ensure_directory(path: Path) -> Path:
    """Create a directory if it does not exist and return the resolved path."""
    path.mkdir(parents=True, exist_ok=True)
    return path.resolve()


def clone_structured_data(data: StructuredData) -> StructuredData:
    """Return a deep copy so transformers can work without mutating the source."""
    return deepcopy(data)


def resolve_input_path(path: str | Path) -> Path:
    """Resolve and validate an input file path."""
    resolved = Path(path).expanduser().resolve()
    if not resolved.exists():
        raise FileNotFoundError(f"Input file does not exist: {resolved}")
    if not resolved.is_file():
        raise IsADirectoryError(f"Input path must be a file: {resolved}")
    return resolved


def infer_input_format(
    input_path: Path,
    supported_formats: tuple[str, ...] = SUPPORTED_INPUT_FORMATS,
) -> str:
    """Infer the input format from the file extension."""
    input_format = input_path.suffix.lower().lstrip(".")
    if not input_format:
        raise ValueError(f"Input file has no extension: {input_path}")
    if input_format not in supported_formats:
        supported_list = ", ".join(sorted(supported_formats))
        raise ValueError(
            f"Unsupported input format '{input_format}'. Supported formats: {supported_list}"
        )
    return input_format


def normalize_output_dir(output_dir: Path | None = None) -> Path:
    """Resolve the output directory and create it if needed."""
    target_dir = output_dir or OUTPUTS_DIR
    return ensure_directory(target_dir.resolve())


def build_output_stem(input_path: Path, sanitization_mode: str, suffix: str) -> str:
    """Build a deterministic output stem for sanitized files and reports."""
    return f"{input_path.stem}_{sanitization_mode}_{suffix}"


def build_sanitized_output_path(
    input_path: Path,
    sanitization_mode: str,
    output_dir: Path | None = None,
) -> Path:
    """Build the target path for the sanitized file export."""
    output_root = normalize_output_dir(output_dir)
    filename = f"{build_output_stem(input_path, sanitization_mode, DEFAULT_SANITIZED_SUFFIX)}{input_path.suffix.lower()}"
    return output_root / filename


def build_report_output_path(
    input_path: Path,
    sanitization_mode: str,
    report_format: str = DEFAULT_REPORT_FORMAT,
    output_dir: Path | None = None,
) -> Path:
    """Build the target path for the audit report."""
    output_root = normalize_output_dir(output_dir)
    filename = f"{build_output_stem(input_path, sanitization_mode, DEFAULT_REPORT_SUFFIX)}.{report_format}"
    return output_root / filename


def format_field_path(field_path: FieldPath) -> str:
    """Convert a tuple-based field path into a readable string."""
    if not field_path:
        return "<root>"

    parts: list[str] = []
    for part in field_path:
        if isinstance(part, int):
            parts.append(f"[{part}]")
        elif not parts:
            parts.append(str(part))
        else:
            parts.append(f".{part}")
    return "".join(parts)


def build_safe_preview(value: str, visible_chars: int = 2) -> str:
    """Create a non-sensitive preview suitable for reports and logs."""
    if len(value) <= visible_chars * 2:
        return "*" * len(value)
    return f"{value[:visible_chars]}***{value[-visible_chars:]}"
