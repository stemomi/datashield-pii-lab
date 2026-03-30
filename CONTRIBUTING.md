# Contributing

Thanks for helping improve DataShield PII Lab.

This project is meant to stay practical, local-first, and safe for privacy-focused demos and experiments.

## Development Setup

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -e ".[dev,db]"
```

If you prefer the older requirements-based workflow:

```bash
pip install -r requirements-dev.txt
```

## Running The Project

Examples:

```bash
datashield scan samples/sample_customers.csv
datashield sanitize samples/sample_customers.csv --mode mask
datashield db --url "sqlite:///example.db" --query "select * from customers"
```

## Running Tests

```bash
python -m pytest -q
```

## Contribution Guidelines

- Use synthetic data only. Never add real PII, secrets, or production exports to the repository.
- Keep changes focused. Small, reviewable pull requests are easier to verify.
- Add or update tests when behavior changes.
- Update the README when CLI usage, supported entities, outputs, or setup steps change.
- Preserve the local-first design. Network-dependent behavior should stay optional and explicit.
- Prefer clear, auditable logic over hidden magic, especially in detection and sanitization code.

## If You Add New Detection Logic

Please update the related parts of the repository together:

- detector implementation
- sample input data when relevant
- sanitization behavior if the new entity should be transformable
- tests
- README documentation

## Pull Request Checklist

Before opening a pull request, make sure you have:

- run the test suite locally
- kept example data synthetic
- avoided committing generated output files unless they are intentional demo artifacts
- documented any user-visible behavior changes

## Style Notes

- Favor small, readable functions and explicit names.
- Keep comments concise and useful.
- Preserve structure when sanitizing CSV and JSON content.
- Prefer deterministic behavior in tests and avoid external network dependencies in the default test suite.

