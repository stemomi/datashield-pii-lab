"""Command-line interface for DataShield PII Lab."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any

from .config import APP_NAME, SUPPORTED_SANITIZATION_MODES
from .config_loader import CliConfig, load_config
from .core.models import PipelineRequest, ReportFormat, SanitizationMode, TransformResult
from .core.pipeline import PipelineOrchestrator
from .core.utils import ensure_directory
from .detectors.presidio_detector import detect_with_presidio
from .detectors.regex_detector import detect_with_regex
from .ingestors.csv_ingestor import load_csv
from .ingestors.db_ingestor import load_db
from .ingestors.json_ingestor import load_json
from .ingestors.pdf_ingestor import load_pdf
from .ingestors.sql_ingestor import load_sql
from .ingestors.txt_ingestor import load_txt
from .reporting.html_report import build_html_report
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
    parser.add_argument(
        "--config",
        help="Optional JSON or YAML config file.",
    )
    parser.add_argument(
        "--detector",
        choices=["regex", "presidio"],
        default="regex",
        help="Detection engine to use.",
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
    sanitize_parser.add_argument(
        "--report-format",
        default=ReportFormat.JSON.value,
        choices=[format.value for format in ReportFormat],
        help="Report format to generate",
    )

    report_parser = subparsers.add_parser(
        "report", help="Generate a report for an input file."
    )
    report_parser.add_argument("input_path", help="Path to the input file")
    report_parser.add_argument(
        "--mode",
        default=SanitizationMode.MASK.value,
        choices=SUPPORTED_SANITIZATION_MODES,
        help="Sanitization mode to include in the report",
    )
    report_parser.add_argument(
        "--report-format",
        default=ReportFormat.JSON.value,
        choices=[format.value for format in ReportFormat],
        help="Report format to generate",
    )

    batch_parser = subparsers.add_parser(
        "batch", help="Process a folder of files in batch."
    )
    batch_parser.add_argument("folder", help="Folder to scan")
    batch_parser.add_argument(
        "--action",
        choices=["scan", "sanitize", "report"],
        default="scan",
        help="Batch action to run",
    )
    batch_parser.add_argument(
        "--mode",
        default=SanitizationMode.MASK.value,
        choices=SUPPORTED_SANITIZATION_MODES,
        help="Sanitization mode for batch sanitize/report",
    )
    batch_parser.add_argument(
        "--report-format",
        default=ReportFormat.JSON.value,
        choices=[format.value for format in ReportFormat],
        help="Report format to generate",
    )

    db_parser = subparsers.add_parser("db", help="Scan a database query.")
    db_parser.add_argument("--url", required=True, help="Database connection URL")
    db_parser.add_argument("--query", required=True, help="SQL query to execute")
    db_parser.add_argument(
        "--mode",
        default=SanitizationMode.MASK.value,
        choices=SUPPORTED_SANITIZATION_MODES,
        help="Sanitization mode to apply",
    )
    db_parser.add_argument(
        "--report-format",
        default=ReportFormat.JSON.value,
        choices=[format.value for format in ReportFormat],
        help="Report format to generate",
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

    config = load_config(Path(args.config)) if args.config else None
    detector_name = _resolve_detector(args.detector, config)

    if args.command == "scan":
        return _handle_scan(Path(args.input_path), detector_name)
    if args.command == "sanitize":
        return _handle_sanitize(
            Path(args.input_path),
            SanitizationMode(args.mode),
            ReportFormat(args.report_format),
            detector_name,
            config,
        )
    if args.command == "report":
        return _handle_report(
            Path(args.input_path),
            SanitizationMode(args.mode),
            ReportFormat(args.report_format),
            detector_name,
            config,
        )
    if args.command == "batch":
        return _handle_batch(
            Path(args.folder),
            args.action,
            SanitizationMode(args.mode),
            ReportFormat(args.report_format),
            detector_name,
            config,
        )
    if args.command == "db":
        return _handle_db(
            args.url,
            args.query,
            SanitizationMode(args.mode),
            ReportFormat(args.report_format),
            detector_name,
            config,
        )

    parser.print_help()
    return 0


def _resolve_detector(detector: str, config: CliConfig | None) -> str:
    if config and config.detector:
        return config.detector
    return detector


def _select_detector(name: str):
    if name == "presidio":
        return detect_with_presidio
    return detect_with_regex


def _build_orchestrator(transformer, detector_name: str, report_format: ReportFormat) -> PipelineOrchestrator:
    reporter = build_html_report if report_format is ReportFormat.HTML else build_json_report
    return PipelineOrchestrator(
        ingestors={
            "csv": load_csv,
            "json": load_json,
            "txt": load_txt,
            "pdf": load_pdf,
            "sql": load_sql,
        },
        detector=_select_detector(detector_name),
        transformer=transformer,
        reporter=reporter,
    )


def _apply_config_defaults(
    mode: SanitizationMode,
    report_format: ReportFormat,
    config: CliConfig | None,
) -> tuple[SanitizationMode, ReportFormat, Path | None]:
    if config is None:
        return mode, report_format, None
    resolved_mode = config.sanitization_mode or mode
    resolved_format = config.report_format or report_format
    return resolved_mode, resolved_format, config.output_dir


def _handle_scan(input_path: Path, detector_name: str) -> int:
    orchestrator = _build_orchestrator(_noop_transformer, detector_name, ReportFormat.JSON)
    result = orchestrator.run(
        PipelineRequest(input_path=input_path, sanitization_mode=SanitizationMode.MASK)
    )

    print("Scan completed.")
    print(f"Input: {result.source.input_path.name}")
    print(f"Entities found: {len(result.detections)}")
    for entity_type, count in sorted(result.entity_counts.items()):
        print(f"- {entity_type}: {count}")
    return 0


def _handle_sanitize(
    input_path: Path,
    mode: SanitizationMode,
    report_format: ReportFormat,
    detector_name: str,
    config: CliConfig | None,
) -> int:
    mode, report_format, output_dir = _apply_config_defaults(mode, report_format, config)
    orchestrator = _build_orchestrator(apply_sanitization, detector_name, report_format)
    result = orchestrator.run(
        PipelineRequest(
            input_path=input_path,
            sanitization_mode=mode,
            report_format=report_format,
            output_dir=output_dir,
        )
    )

    output_path = _resolve_output_path(result.source.input_format, result.sanitized_output_path)
    _write_sanitized_output(result.source.input_format, result.transform_result.content, output_path)

    report = _update_report_paths(result.report, output_path)
    _write_report(report, result.report_output_path, report_format)

    print("Sanitization completed.")
    print(f"Output file: {output_path}")
    print(f"Report file: {result.report_output_path}")
    return 0


def _handle_report(
    input_path: Path,
    mode: SanitizationMode,
    report_format: ReportFormat,
    detector_name: str,
    config: CliConfig | None,
) -> int:
    mode, report_format, output_dir = _apply_config_defaults(mode, report_format, config)
    orchestrator = _build_orchestrator(_noop_transformer, detector_name, report_format)
    result = orchestrator.run(
        PipelineRequest(
            input_path=input_path,
            sanitization_mode=mode,
            report_format=report_format,
            output_dir=output_dir,
        )
    )

    _write_report(result.report, result.report_output_path, report_format)

    print("Report generated.")
    print(f"Report file: {result.report_output_path}")
    return 0


def _handle_batch(
    folder: Path,
    action: str,
    mode: SanitizationMode,
    report_format: ReportFormat,
    detector_name: str,
    config: CliConfig | None,
) -> int:
    if not folder.exists() or not folder.is_dir():
        raise FileNotFoundError(f"Folder not found: {folder}")

    mode, report_format, _ = _apply_config_defaults(mode, report_format, config)

    supported = {"csv", "json", "txt", "pdf", "sql"}
    files = [path for path in folder.iterdir() if path.suffix.lower().lstrip(".") in supported]

    if not files:
        print("No supported files found.")
        return 0

    for path in files:
        if action == "scan":
            _handle_scan(path, detector_name)
        elif action == "report":
            _handle_report(path, mode, report_format, detector_name, config)
        else:
            _handle_sanitize(path, mode, report_format, detector_name, config)

    print(f"Batch completed for {len(files)} files.")
    return 0


def _handle_db(
    connection_url: str,
    query: str,
    mode: SanitizationMode,
    report_format: ReportFormat,
    detector_name: str,
    config: CliConfig | None,
) -> int:
    mode, report_format, output_dir = _apply_config_defaults(mode, report_format, config)
    rows = load_db(query, connection_url)

    orchestrator = PipelineOrchestrator(
        ingestors={"db": lambda _: rows},
        detector=_select_detector(detector_name),
        transformer=apply_sanitization,
        reporter=build_html_report if report_format is ReportFormat.HTML else build_json_report,
    )

    result = orchestrator.run(
        PipelineRequest(
            input_path=Path("database"),
            sanitization_mode=mode,
            report_format=report_format,
            output_dir=output_dir,
            source_format="db",
        )
    )

    _write_report(result.report, result.report_output_path, report_format)

    print("Database scan completed.")
    print(f"Report file: {result.report_output_path}")
    return 0


def _noop_transformer(source, detections, sanitization_mode) -> TransformResult:
    return TransformResult(content=source.content, applied_transformations=[])


def _update_report_paths(report: dict[str, Any] | str, output_path: Path) -> dict[str, Any] | str:
    if not isinstance(report, dict):
        return report
    report["output_file"] = str(output_path)
    planned = report.get("planned_outputs")
    if isinstance(planned, dict):
        planned["sanitized_file"] = str(output_path)
    return report


def _resolve_output_path(input_format: str, output_path: Path) -> Path:
    if input_format == "pdf" and output_path.suffix.lower() == ".pdf":
        return output_path.with_suffix(".txt")
    return output_path


def _write_report(report: dict[str, Any] | str, output_path: Path, report_format: ReportFormat) -> None:
    ensure_directory(output_path.parent)
    if report_format is ReportFormat.HTML:
        output_path = output_path.with_suffix(".html")
        if isinstance(report, str):
            output_path.write_text(report, encoding="utf-8")
        else:
            output_path.write_text("<html><body><pre>Invalid HTML report</pre></body></html>", encoding="utf-8")
        return

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
    if input_format in {"txt", "pdf", "sql"}:
        _write_txt(content, output_path)
        return

    raise ValueError(f"Unsupported output format: {input_format}")


def _write_json(content: object, output_path: Path) -> None:
    with output_path.open("w", encoding="utf-8") as handle:
        json.dump(content, handle, ensure_ascii=False, indent=2)


def _write_txt(content: object, output_path: Path) -> None:
    if not isinstance(content, str):
        content = str(content)
    output_path.write_text(content, encoding="utf-8")


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
