"""Command-line interface for DataShield PII Lab."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any

from .config import APP_NAME, SUPPORTED_SANITIZATION_MODES
from .core.models import PipelineRequest, SanitizationMode, TransformResult
from .core.pipeline import PipelineOrchestrator
from .core.utils import ensure_directory
from .detectors.regex_detector import detect_with_regex
from .ingestors.csv_ingestor import load_csv
from .ingestors.json_ingestor import load_json
from .reporting.json_report import build_json_report
from .transformers.sanitizer import apply_sanitization


def build_parser() -> argparse.ArgumentParser:
    """Create the CLI parser with subcommands."""
    parser = argparse.ArgumentParser(
        prog="datashield",
        description="Local-first PII detection and sanitization toolkit.",
    )
    parser.add_argument(
        "--bootstrap-check",
        action="store_true",
        help="Print the current scaffold status.",
    )

    subparsers = parser.add_subparsers(dest="command")

    scan_parser = subparsers.add_parser("scan", help="Scan a file and summarize detections.")
    scan_parser.add_argument("input_path", help="Path to the input file")

    sanitize_parser = subparsers.add_parser(
        "sanitize", help="Sanitize a file using the selected mode."
    )
    sanitize_parser.add_argument("input_path", help="Path to the input file")
    sanitize_parser.add_argument(
        "--mode",
        required=True,
        choices=SUPPORTED_SANITIZATION_MODES,
        help="Sanitization mode to apply",
    )

    report_parser = subparsers.add_parser(
        "report", help="Generate a JSON report for an input file."
    )
    report_parser.add_argument("input_path", help="Path to the input file")
    report_parser.add_argument(
        "--mode",
        default=SanitizationMode.MASK.value,
        choices=SUPPORTED_SANITIZATION_MODES,
        help="Sanitization mode to include in the report",
    )

    return parser


def run(argv: list[str] | None = None) -> int:
    """Run the CLI entry point."""
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.bootstrap_check:
        print(
            f"{APP_NAME} scaffold is ready. Core pipeline architecture is available for concrete integrations."
        )
        return 0

    if args.command == "scan":
        return _handle_scan(Path(args.input_path))
    if args.command == "sanitize":
        return _handle_sanitize(Path(args.input_path), SanitizationMode(args.mode))
    if args.command == "report":
        return _handle_report(Path(args.input_path), SanitizationMode(args.mode))

    parser.print_help()
    return 0


def _build_orchestrator(transformer) -> PipelineOrchestrator:
    return PipelineOrchestrator(
        ingestors={"csv": load_csv, "json": load_json},
        detector=detect_with_regex,
        transformer=transformer,
        reporter=build_json_report,
    )


def _noop_transformer(source, detections, sanitization_mode) -> TransformResult:
    return TransformResult(content=source.content, applied_transformations=[])


def _handle_scan(input_path: Path) -> int:
    orchestrator = _build_orchestrator(_noop_transformer)
    result = orchestrator.run(
        PipelineRequest(input_path=input_path, sanitization_mode=SanitizationMode.MASK)
    )

    print("Scan completed.")
    print(f"Input: {result.source.input_path.name}")
    print(f"Entities found: {len(result.detections)}")
    for entity_type, count in sorted(result.entity_counts.items()):
        print(f"- {entity_type}: {count}")
    return 0


def _handle_sanitize(input_path: Path, mode: SanitizationMode) -> int:
    orchestrator = _build_orchestrator(apply_sanitization)
    result = orchestrator.run(PipelineRequest(input_path=input_path, sanitization_mode=mode))

    _write_sanitized_output(result.source.input_format, result.transform_result.content, result.sanitized_output_path)
    _write_report(result.report, result.report_output_path)

    print("Sanitization completed.")
    print(f"Output file: {result.sanitized_output_path}")
    print(f"Report file: {result.report_output_path}")
    return 0


def _handle_report(input_path: Path, mode: SanitizationMode) -> int:
    orchestrator = _build_orchestrator(_noop_transformer)
    result = orchestrator.run(PipelineRequest(input_path=input_path, sanitization_mode=mode))

    _write_report(result.report, result.report_output_path)

    print("Report generated.")
    print(f"Report file: {result.report_output_path}")
    return 0


def _write_report(report: dict[str, Any], output_path: Path) -> None:
    ensure_directory(output_path.parent)
    with output_path.open("w", encoding="utf-8") as handle:
        json.dump(report, handle, ensure_ascii=False, indent=2)


def _write_sanitized_output(
    input_format: str,
    content: object,
    output_path: Path,
) -> None:
    ensure_directory(output_path.parent)

    if input_format == "csv":
        _write_csv(content, output_path)
        return
    if input_format == "json":
        _write_json(content, output_path)
        return

    raise ValueError(f"Unsupported output format: {input_format}")


def _write_json(content: object, output_path: Path) -> None:
    with output_path.open("w", encoding="utf-8") as handle:
        json.dump(content, handle, ensure_ascii=False, indent=2)


def _write_csv(content: object, output_path: Path) -> None:
    if not isinstance(content, list):
        raise ValueError("CSV output expects a list of row dictionaries.")

    rows = [row for row in content if isinstance(row, dict)]
    fieldnames: list[str] = []
    seen = set()
    for row in rows:
        for key in row.keys():
            if key not in seen:
                fieldnames.append(key)
                seen.add(key)

    with output_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
if __name__ == "__main__":
    raise SystemExit(run())
