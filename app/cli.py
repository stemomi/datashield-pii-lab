"""Command-line interface scaffolding for DataShield PII Lab."""

from __future__ import annotations

import argparse

from .config import APP_NAME


def build_parser() -> argparse.ArgumentParser:
    """Create the base CLI parser used during the bootstrap phase."""
    parser = argparse.ArgumentParser(
        prog="datashield",
        description="Local-first PII detection and sanitization toolkit.",
    )
    parser.add_argument(
        "--bootstrap-check",
        action="store_true",
        help="Print the current scaffold status.",
    )
    return parser


def run(argv: list[str] | None = None) -> int:
    """Run the CLI scaffold."""
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.bootstrap_check:
        print(f"{APP_NAME} scaffold is ready. Next roadmap step: CSV ingestion.")
        return 0

    parser.print_help()
    return 0
