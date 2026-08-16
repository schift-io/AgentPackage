# Security Policy

## Reporting a vulnerability

If you find a security issue in the APM format, kit, or any file in this
repository, please report it privately:

**Email:** security@schift.io

Do NOT open a public issue for security vulnerabilities.

We will acknowledge your report within 48 hours and provide a timeline for
a fix. If the issue affects published `.apm` packages or the content hash
algorithm, we will coordinate disclosure.

## Scope

This repo contains the **package format specification and build tools**.
It does not contain:

- Schift's managed runtime (Agent Hub)
- Schift's vector search engine
- Schift's API server
- Any deployment credentials or secrets

If you find a vulnerability in Schift's hosted services, report it to
security@schift.io with "Hosted Service" in the subject line.

## Supported versions

| Version | Supported |
|---|---|
| SPEC.md v1 (current) | Yes |
| kit 0.x | Yes |
| Older | No |
