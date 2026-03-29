"""Project-wide configuration values."""

from __future__ import annotations

from pathlib import Path

APP_NAME = "DataShield PII Lab"
PROJECT_ROOT = Path(__file__).resolve().parent.parent
SAMPLES_DIR = PROJECT_ROOT / "samples"
OUTPUTS_DIR = PROJECT_ROOT / "outputs"

DEFAULT_REPORT_FORMAT = "json"
DEFAULT_SANITIZED_SUFFIX = "sanitized"
DEFAULT_REPORT_SUFFIX = "report"

SUPPORTED_INPUT_FORMATS = ("csv", "json", "txt")
SUPPORTED_REPORT_FORMATS = (DEFAULT_REPORT_FORMAT,)
SUPPORTED_ENTITY_TYPES = ("EMAIL", "PHONE", "TAX_CODE", "IBAN")
SUPPORTED_SANITIZATION_MODES = ("mask", "redact")
