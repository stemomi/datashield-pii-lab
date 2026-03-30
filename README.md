# DataShield PII Lab

DataShield PII Lab is a local-first privacy engineering project focused on detecting and sanitizing sensitive personal data in structured files. The MVP is designed as a practical defensive security tool for safe data sharing, data minimization, and audit-friendly processing.

## Project Overview

The tool reads supported input files, detects selected categories of personally identifiable information (PII), classifies each match, applies a protection strategy, and writes both a sanitized output file and a machine-readable report.

## Features

- Local-first processing with no required external API calls
- Detection pipeline for common structured PII in CSV, JSON, TXT, PDF, and SQL dumps
- Regex and field-context detection for names, addresses, dates, and IPs
- Sanitization modes for masking, redaction, and pseudonymization
- JSON and HTML reporting for auditing and analysis
- Optional Presidio integration for advanced entity recognition
- Batch folder scanning and database query scanning

## Supported Formats

Current support:

- CSV
- JSON
- TXT
- PDF (text extraction)
- SQL dumps

## Supported PII Types

Current support:

- `EMAIL`
- `PHONE`
- `TAX_CODE`
- `IBAN`
- `BIRTH_DATE`
- `ADDRESS`
- `IP_ADDRESS`
- `PERSON_NAME`

## Sanitization Modes

- `mask`: partially hide a value while preserving part of its structure
- `redact`: replace a value with a labeled placeholder such as `[REDACTED_EMAIL]`
- `pseudonymize`: deterministic mapping to identifiers such as `EMAIL_001`

## Installation

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

## Usage Examples

Bootstrap check:

```bash
python -m app.main --bootstrap-check
```

CLI usage:

```bash
python -m app.cli scan samples/sample_customers.csv
python -m app.cli sanitize samples/sample_customers.csv --mode mask
python -m app.cli sanitize samples/sample_customers.json --mode redact
python -m app.cli report samples/sample_customers.csv --mode mask
```

The `report` command writes only the audit report and does not create a sanitized export.

Batch scan:

```bash
python -m app.cli batch samples --action scan
```

Database scan:

```bash
python -m app.cli db --url "sqlite:///example.db" --query "select * from customers"
```

## Architecture

The repository is organized around a simple privacy pipeline:

1. `ingestors` load supported file formats.
2. `detectors` identify candidate PII.
3. `transformers` apply the selected protection mode.
4. `reporting` generates audit artifacts.
5. `core` contains shared models, orchestration, and utility helpers.

## Example Output

Sanitized value examples:

- `mario.rossi@gmail.com` -> `m***o.r***i@gmail.com`
- `+39 3331234567` -> `+39 333****567`
- `1985-06-14` -> `1**5-**-**`
- `Via Roma 10` -> `V*a R**a **`
- `192.168.1.42` -> `192.***.***.42`
- `Mario Rossi` -> `M***o R***i`
- `IT60X0542811101000000123456` -> `[REDACTED_IBAN]`

Report output example:

```json
{
  "input_file": "sample_customers.csv",
  "sanitization_mode": "mask",
  "entities_found": 24,
  "entity_counts": {
    "ADDRESS": 3,
    "BIRTH_DATE": 3,
    "EMAIL": 3,
    "IBAN": 3,
    "IP_ADDRESS": 3,
    "PERSON_NAME": 3,
    "PHONE": 3,
    "TAX_CODE": 3
  },
  "output_file": "outputs/sample_customers_mask_sanitized.csv"
}
```

## Security And Privacy Design Choices

- Processing stays local by default
- Sanitized exports and reports are separated from source samples
- Audit reporting is part of the main workflow, not an afterthought
- The initial design favors explicit, testable regex logic before advanced integrations

## Limitations

- Detection still relies on heuristics and field context, so false positives and false negatives are possible
- Name and address detection is intentionally conservative to avoid overmatching
- PDF extraction quality depends on the source document
- Database support requires SQLAlchemy drivers

## Roadmap

Completed in the current release:

- CSV and JSON ingestion
- Regex-based detection for identifiers, dates, and IP addresses
- Field-aware detection for names and addresses
- Masking, redaction, and baseline pseudonymization
- Sanitized file export
- JSON reporting
- CLI commands and automated tests

Next steps:

- Stronger TXT, PDF, and SQL workflows beyond the current baseline support
- More advanced Presidio-backed detection profiles
- Batch processing improvements and optional dashboard or web UI
- Custom detection rules and project-level configuration profiles
- Additional entity families such as organizations, document IDs, and domain-specific records
