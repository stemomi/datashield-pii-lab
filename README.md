# DataShield PII Lab

DataShield PII Lab is a local-first privacy engineering project focused on detecting and sanitizing sensitive personal data in structured files. The MVP is designed as a practical defensive security tool for safe data sharing, data minimization, and audit-friendly processing.

## Project Overview

The tool reads supported input files, detects selected categories of personally identifiable information (PII), classifies each match, applies a protection strategy, and writes both a sanitized output file and a machine-readable report.

## Features

- Local-first processing with no required external API calls
- Detection pipeline for common structured PII in CSV, JSON, and TXT files
- Sanitization modes for masking and redaction
- JSON reporting for auditing and analysis
- Extensible project structure for future PDF, TXT, SQL, and pseudonymization support

## Supported Formats

Current MVP support:

- CSV
- JSON
- TXT

Planned for later phases:

- PDF
- SQL exports

## Supported PII Types

MVP target entities:

- `EMAIL`
- `PHONE`
- `TAX_CODE`
- `IBAN`

Planned for later phases:

- `BIRTH_DATE`
- `ADDRESS`
- `IP_ADDRESS`
- `PERSON_NAME`

## Sanitization Modes

- `mask`: partially hide a value while preserving part of its structure
- `redact`: replace a value with a labeled placeholder such as `[REDACTED_EMAIL]`

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
- `IT60X0542811101000000123456` -> `[REDACTED_IBAN]`

Report output example:

```json
{
  "input_file": "sample_customers.csv",
  "sanitization_mode": "mask",
  "entities_found": 12,
  "entity_counts": {
    "EMAIL": 3,
    "PHONE": 3,
    "TAX_CODE": 3,
    "IBAN": 3
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

- Detection relies on regex heuristics and may need refinement
- CSV, JSON, and TXT are the only MVP input targets
- PDF and SQL ingestion are placeholders for later phases

## Roadmap

Implementation order for the MVP:

1. Repository setup
2. CSV ingestor
3. JSON ingestor
4. Email regex detection
5. Phone regex detection
6. Tax code and IBAN regex detection
7. Entity model
8. JSON reporting
9. Masking
10. Redaction
11. Sanitized CSV and JSON export
12. CLI commands
13. Tests
14. Documentation improvements
15. Extended formats and pseudonymization
