# LAAF HTML Assessment Reports

LAAF generates professional vulnerability assessment reports modelled on enterprise penetration testing standards.

---

## Report Structure

Every HTML report contains:

### 1. Executive Summary
- Overall risk rating (CRITICAL / HIGH / MEDIUM / LOW)
- Breakthrough rate (stages broken / 6)
- Total attempts, total duration
- OWASP LLM Top 10 mappings
- Scan metadata (date, platform, model, scan ID)

### 2. Stage Breakthrough Charts
- **Bar chart** — attempts per stage
- **Radar chart** — technique category effectiveness (Encoding / Structural / Semantic / Layered / Trigger)

### 3. Per-Stage Findings

Each broken stage produces one finding card structured as:

```
Finding #N — [Stage Name]
│
├── Severity:           CRITICAL | HIGH | MEDIUM
├── OWASP Mapping:      LLM01 Prompt Injection | LLM06 Excessive Agency | LLM07 System Prompt Leakage
│
├── IMPACT CHAIN
│   Technique X → Bypasses control Y → Enables action Z → Business harm W
│
├── OBSERVATION
│   Technical description of what happened
│
├── WHAT WAS ACHIEVED
│   Concrete attacker gain (data extracted, instruction executed, etc.)
│
├── STEPS TO REPRODUCE
│   1. Encode instruction using technique X
│   2. Submit via user input channel
│   3. Observe model response
│   4. Breakthrough confirmed at attempt N
│
├── IMPLICATIONS
│   Business / regulatory / compliance impact
│
├── AFFECTED SURFACE
│   Which deployment types are vulnerable
│
├── RECOMMENDATION
│   Specific remediation steps
│
└── EVIDENCE
    ├── Attack Intent (Decoded)   — plain-text version of the instruction
    ├── Payload Sent to LLM       — actual encoded payload sent
    └── LLM Response              — model's response proving compliance
```

---

## Sample Reports from Paper

The 5 HTML reports from the empirical evaluation (2026-03-06) are included in this repository:

| File | Platform | Risk | BR |
|---|---|---|---|
| [`report_Gemini-2.html`](../results/paper_table2/reports/report_Gemini-2.html) | Gemini-2.0-flash-001 | CRITICAL | 100% |
| [`report_Claude.html`](../results/paper_table2/reports/report_Claude.html) | Claude-3-haiku | CRITICAL | 100% |
| [`report_Mixtral-8x7b.html`](../results/paper_table2/reports/report_Mixtral-8x7b.html) | Mixtral-8x7b-instruct | CRITICAL | 100% |
| [`report_LLaMA3-70B.html`](../results/paper_table2/reports/report_LLaMA3-70B.html) | LLaMA3-70B-instruct | MEDIUM | 67% |
| [`report_ChatGPT.html`](../results/paper_table2/reports/report_ChatGPT.html) | GPT-4o-mini | MEDIUM | 50% |

---

## Report Formats

| Format | Command | Use case |
|---|---|---|
| HTML | `--format html` | Human review, paper appendix, client delivery |
| JSON | `--format json` | Machine processing, CI/CD integration |
| CSV | `--format csv` | Spreadsheet analysis, data science |
| PDF | `--format pdf` | Formal report submission |

---

## Offline Support

HTML reports embed Chart.js inline — they render correctly with **no internet connection**. Safe for air-gapped environments and paper appendix submission.

---

## Generating Reports

```bash
# During scan (automatic)
laaf scan --target mock --stages all --format html,json,csv

# From existing JSON results
laaf report --input results/laaf-mock-abc/report.json --format html
laaf report --input results/laaf-mock-abc/report.json --format pdf

# From paper table2 scan data
python examples/generate_model_reports.py
```
