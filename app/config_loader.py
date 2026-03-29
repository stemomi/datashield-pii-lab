"""Configuration loader for CLI runs."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError:
    yaml = None

from .core.models import ReportFormat, SanitizationMode


@dataclass(frozen=True)
class CliConfig:
    """Configuration loaded from a JSON or YAML file."""

    sanitization_mode: SanitizationMode | None = None
    report_format: ReportFormat | None = None
    output_dir: Path | None = None
    detector: str | None = None


def load_config(path: Path | None) -> CliConfig | None:
    """Load a CLI configuration file if provided."""
    if path is None:
        return None

    if not path.exists():
        raise FileNotFoundError(f"Config file not found: {path}")

    if path.suffix.lower() in {".yaml", ".yml"}:
        if yaml is None:
            raise ImportError("pyyaml is required for YAML config files. Install it with 'pip install pyyaml'.")
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    else:
        data = json.loads(path.read_text(encoding="utf-8"))

    return _parse_config(data)


def _parse_config(data: dict[str, Any]) -> CliConfig:
    """Normalize raw config data into a CliConfig instance."""
    output_dir = data.get("output_dir")
    report_format = data.get("report_format")
    sanitization_mode = data.get("sanitization_mode")
    detector = data.get("detector")

    return CliConfig(
        sanitization_mode=SanitizationMode(sanitization_mode)
        if sanitization_mode is not None
        else None,
        report_format=ReportFormat(report_format) if report_format is not None else None,
        output_dir=Path(output_dir) if output_dir else None,
        detector=detector,
    )
