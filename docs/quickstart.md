# LAAF Quick Start Guide

## Prerequisites

- Python 3.11+
- An API key from any supported provider (or use the built-in mock — no key needed)

---

## 1. Install

```bash
git clone https://github.com/qorvexconsulting1/laaf
cd laaf
pip install -e .
```

Verify installation:
```bash
laaf --version
# LAAF v0.1.0
```

---

## 2. Test Without an API Key (Mock Platform)

The mock platform simulates a vulnerable LLM — no API key, no cost, instant results.

```bash
# Dry run — shows generated payloads only, no scan
laaf scan --target mock --dry-run

# Full scan — runs all 6 stages, generates HTML + CSV + JSON report
laaf scan --target mock --stages all --payloads 100 --output results/
```

Open the generated HTML report:
```
results/laaf-mock-XXXXXXXX/report_laaf-mock-XXXXXXXX.html
```

---

## 3. Configure API Keys

Copy the example environment file:
```bash
cp .env.example .env
```

Edit `.env` and add your keys:
```bash
OPENROUTER_API_KEY=sk-or-...     # recommended — covers all models
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
GOOGLE_API_KEY=...
```

Or export inline:
```bash
export OPENROUTER_API_KEY=sk-or-...
```

---

## 4. Run a Real Scan

### OpenRouter (recommended — one key, all models)
```bash
export OPENROUTER_API_KEY=sk-or-...

# Test GPT-4o-mini
laaf scan --target openrouter --model openai/gpt-4o-mini --stages all --payloads 100

# Test Claude
laaf scan --target openrouter --model anthropic/claude-3-haiku --stages all

# Test Gemini
laaf scan --target openrouter --model google/gemini-2.0-flash-001 --stages all
```

### Direct Platform APIs
```bash
# OpenAI
export OPENAI_API_KEY=sk-...
laaf scan --target openai --model gpt-4o --stages all --payloads 100

# Anthropic
export ANTHROPIC_API_KEY=sk-ant-...
laaf scan --target anthropic --model claude-3-haiku-20240307 --stages all

# Google
export GOOGLE_API_KEY=...
laaf scan --target google --model gemini-2.0-flash --stages all
```

---

## 5. Understand the Output

A scan produces:
```
results/laaf-openrouter-XXXXXXXX/
├── report_laaf-openrouter-XXXXXXXX.csv    # per-payload results
├── report_laaf-openrouter-XXXXXXXX.json   # full machine-readable results
└── report_laaf-openrouter-XXXXXXXX.html   # professional assessment report
```

The HTML report contains:

- **Executive Summary** — overall risk rating, breakthrough rate, total attempts
- **Stage Breakdown** — bar/radar charts per technique category
- **Per-Stage Findings** — structured findings with:
  - Impact Chain (Technique → Bypasses → Enables → Business harm)
  - Steps to Reproduce
  - Evidence (decoded payload + LLM response)
  - Recommendation

---

## 6. Explore the Taxonomy

```bash
# Show all 49 techniques
laaf list-techniques

# Filter by category
laaf list-techniques --category encoding
laaf list-techniques --category semantic
laaf list-techniques --category layered
laaf list-techniques --category trigger
laaf list-techniques --category structural

# Machine-readable output
laaf list-techniques --json
```

---

## 7. Generate a Report from Existing Results

```bash
# From JSON scan output
laaf report --input results/laaf-openrouter-abc123/report.json --format html
laaf report --input results/laaf-openrouter-abc123/report.json --format pdf
```

---

## 8. Start the Web Dashboard

```bash
laaf serve --host 0.0.0.0 --port 8080
```

Open:
- Dashboard: `http://localhost:8080/dashboard`
- API docs:  `http://localhost:8080/docs`
- Health:    `http://localhost:8080/health`

---

## 9. Docker

```bash
cp .env.example .env    # add API keys
docker compose up
```

Access at `http://localhost:8080`

---

## 10. Run the Paper's Multi-Model Scan

To reproduce the paper's Table 2 results:

```bash
export OPENROUTER_API_KEY=sk-or-...
python examples/paper_table2_scan.py
```

Results are saved to `results/paper_verification_v<N>/table2_results.json`.

Then regenerate all 5 HTML reports:
```bash
python examples/generate_model_reports.py
```

---

## Supported Platforms

| Target flag | Provider | Models |
|---|---|---|
| `--target mock` | Built-in mock | Any (testing only) |
| `--target openrouter` | OpenRouter | All major models |
| `--target openai` | OpenAI | gpt-4o, gpt-4o-mini, etc. |
| `--target anthropic` | Anthropic | claude-3-haiku, claude-3-sonnet, etc. |
| `--target google` | Google | gemini-2.0-flash, gemini-1.5-pro, etc. |
| `--target huggingface` | HuggingFace | Any HF Inference API model |
| `--target azure` | Azure OpenAI | Any Azure-deployed model |
