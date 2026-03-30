# Security Policy

## Scope

DataShield PII Lab processes sensitive-looking data by design, so secure handling matters even in a demo or portfolio context.

This repository should contain only synthetic or clearly non-production data.

Do not commit:

- real personal data
- production database dumps
- secrets, API keys, or credentials
- logs or reports containing live customer information

If real data is committed by mistake, treat it as a security incident and remove it as quickly as possible.

## Supported Versions

Security fixes are handled on a best-effort basis for the current `master` branch.

| Version | Supported |
| --- | --- |
| `master` | Yes |
| Older snapshots and local forks | No guarantee |

## Reporting A Vulnerability

Please do not open a public issue for an undisclosed vulnerability, especially if it could expose real PII or sensitive infrastructure details.

Preferred reporting path:

1. Use GitHub private vulnerability reporting from the repository Security tab, if it is enabled.
2. If private reporting is not available, open a minimal public issue without secrets and ask for a private contact channel.

When reporting, include:

- the affected commit, branch, or version
- clear reproduction steps
- expected impact
- any mitigation you already tested
- sanitized screenshots, logs, or samples only

## Disclosure Expectations

Reports will be reviewed on a best-effort basis.

The general goal is:

1. confirm the issue
2. reduce exposure
3. prepare a fix
4. disclose publicly only after a patch or clear mitigation exists

## Safe Research Guidelines

If you are testing the project:

- use local, synthetic datasets only
- avoid sending repository data to third-party services unless you explicitly intend to test that integration
- avoid destructive testing against systems you do not own
- do not include exploit payloads that expose live data in issues or pull requests
