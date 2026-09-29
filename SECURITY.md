# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 1.0.x   | :white_check_mark: |

## Reporting a Vulnerability

If you discover a security vulnerability within the Tri-Agent Orchestrator framework or agent sandbox:

1. **Do not submit a public issue.**
2. Report the vulnerability privately via GitHub Security Advisories.
3. Include reproducible steps and protocol payloads.

## Operational Safeguards Notice
This project implements loop detection and human approval gates for high-risk actions (`DELETE_CRITICAL_DATA`, `EXECUTE_PAYMENT`, `PUBLIC_PUBLISH`). Do not bypass these safeguards in production.
