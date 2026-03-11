# Security Policy

## Authorised Use Only

LAAF is designed exclusively for **authorised security testing** of AI systems. Use of this framework against systems without explicit written authorisation is prohibited.

## Reporting Vulnerabilities

To report a security vulnerability in LAAF itself:

1. **Do NOT** open a public GitHub issue.
2. Email: `hatta@qorvexconsulting.com` with subject `[LAAF Security]`
3. Include: description, reproduction steps, potential impact, and suggested fix.
4. We will acknowledge within 48 hours and aim to release a patch within 14 days.

## Supported Versions

| Version | Supported |
|---------|-----------|
| 0.1.x   | ✅ Yes    |

## Responsible Disclosure

LAAF follows coordinated vulnerability disclosure. Researchers who report valid security issues will be credited in the changelog.

## Usage Guidelines

- Only test systems you own or have explicit written permission to test.
- Set rate limiting to avoid service disruption.
- Exfiltration payloads must target researcher-controlled endpoints only.
- Report discovered vulnerabilities in target LLMs through their official channels.
