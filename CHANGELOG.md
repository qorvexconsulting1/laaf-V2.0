# Changelog

All notable changes to LAAF are documented in this file.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).
LAAF uses [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [0.1.0] — 2026-03-04

### Added

#### Core Framework
- **Persistent Stage Breaker (PSB)** algorithm implementing LPCI lifecycle adversarial search (paper §6.1, Eq. 2)
- **49-technique LPCI taxonomy** across six categories:
  - Encoding (E1–E11): Base64, Hex, Unicode, HTML entities, ROT13, URL, Binary, Octal, Nested-B64, ROT13+B64, Hex+B64
  - Structural (S1–S8): JSON, YAML, Markdown comment, HTML meta, Code block, Token split, XML, PDF metadata
  - Semantic (M1–M8): Formatting request, Compliance reframe, SysInit, ToolMeta, Authority, ISO standard, Trust build, DocConfig
  - Layered (L1–L5): Stacked multi-technique combinations with escalating complexity
  - Trigger (T1–T12): Keyword, compound, timing, cross-session, and steganographic triggers
  - Exfiltration (EX1–EX5): URL parameter, Markdown image, JSON field, steganographic text, tool call argument
- **MutationEngine** with 4 adaptive strategies (encoding, reframe, trigger, compound)
- **ResponseAnalyser** with EXECUTED/BLOCKED/WARNING/UNKNOWN classification
- **PayloadGenerator** with SHA-256 deduplication registry
- **StageEngine** for sequential S1→S6 context loading from YAML configs

#### Platform Adapters
- OpenAI (GPT-4/4o series)
- Anthropic (Claude 3/4 series)
- Google (Gemini 1.5/2.0)
- Azure OpenAI
- HuggingFace (API + local inference)
- OpenRouter (multi-model gateway)
- Copilot Browser (Playwright-based for web-embedded AI)
- Mock platform (deterministic, for testing)

#### CLI
- `laaf scan` — run PSB against any supported platform
- `laaf serve` — start REST API + web dashboard
- `laaf report` — generate reports from existing results
- `laaf list-techniques` — browse taxonomy with category filter
- `laaf validate-config` — validate YAML stage configuration

#### REST API (FastAPI)
- `POST /scans` — launch background PSB scan
- `GET /scans/{id}` — poll scan status and results
- `DELETE /scans/{id}` — remove scan record
- `GET /reports/{id}?format=json|html|pdf|csv` — download reports
- `GET /techniques` — list all 49 techniques
- `GET /health` — service health and technique count

#### Reporting
- JSON report — structured vulnerability assessment with full artifact evidence
- HTML report — interactive Chart.js bar/radar charts with stage heatmap
- PDF report — executive summary using reportlab
- CSV report — tabular data export for SIEM/spreadsheet integration

#### Web Dashboard
- Real-time scan progress via HTMX polling
- Stage breakthrough heatmap
- Technique breakdown charts
- Scan management table

#### Infrastructure
- Multi-stage Dockerfile (Python 3.11-slim)
- Docker Compose configuration
- GitHub Actions CI (pytest + ruff + mypy)
- GitHub Actions release pipeline (tag → PyPI)
- CodeQL security scanning workflow
- GitHub issue and PR templates

#### Documentation
- Architecture overview (`docs/architecture.md`)
- Taxonomy reference (`docs/taxonomy.md`)
- PSB algorithm deep-dive (`docs/stage-breaker.md`)
- Enterprise deployment guide (`docs/enterprise-guide.md`)
- 3 example scripts (basic, enterprise, custom platform)

### References
- LAAF paper: arXiv:2507.10457 — Atta et al., Qorvex Research, 2026
- OWASP Top 10 for LLM Applications
- NIST AI Risk Management Framework

---

## [Unreleased]

### Planned
- Persistent database backend (SQLite/PostgreSQL) for scan history
- Plugin entry points for 3rd-party technique modules
- SARIF output format for GitHub Advanced Security integration
- Async multi-target parallel scanning
- LlamaGuard integration for automated remediation testing
