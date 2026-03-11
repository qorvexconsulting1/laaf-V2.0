# Testing Your Own LLM with LAAF

LAAF is designed as a **day-to-day security testing tool** — not just a research instrument. Any LLM can be tested: cloud APIs, self-hosted models, internal enterprise systems, or AI products under development.

This guide covers every integration pattern.

---

## Which Pattern Fits Your Setup?

| Your LLM | Use This |
|---|---|
| OpenAI / Anthropic / Gemini / Azure | Built-in `--target` flag |
| Local model via Ollama, LM Studio, vLLM | `OllamaPlatform` or `OpenAICompatiblePlatform` |
| Private company API | `EnterpriseInternalPlatform` |
| AWS Bedrock | `BedrockPlatform` |
| Any other system | Subclass `AbstractPlatform` (5-minute setup) |

---

## Option 1 — Built-in Targets (No Code Required)

For the most common cloud LLMs, just pass a flag:

```bash
# OpenAI
export OPENAI_API_KEY=sk-...
laaf scan --target openai --model gpt-4o --stages all

# Anthropic
export ANTHROPIC_API_KEY=sk-ant-...
laaf scan --target anthropic --model claude-3-haiku-20240307 --stages all

# Google Gemini
export GOOGLE_API_KEY=...
laaf scan --target google --model gemini-2.0-flash --stages all

# Azure OpenAI
export AZURE_OPENAI_API_KEY=...
export AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
laaf scan --target azure --model gpt-4o --stages all

# OpenRouter (one key → all models)
export OPENROUTER_API_KEY=sk-or-...
laaf scan --target openrouter --model openai/gpt-4o-mini --stages all
```

---

## Option 2 — Local / Self-Hosted Models

### Ollama (Free, No API Key)

```bash
# Install Ollama: https://ollama.com
ollama pull llama3.2
ollama pull mistral
ollama pull phi4
```

```python
# examples/custom_platform.py → uncomment OllamaPlatform
platform = OllamaPlatform(model="llama3.2")
```

```bash
python examples/custom_platform.py
```

### vLLM or LM Studio

Any server that speaks the OpenAI API format:

```python
platform = OpenAICompatiblePlatform(
    base_url="http://your-gpu-server:8000/v1",
    model="meta-llama/Llama-3.1-70B-Instruct",
    api_key="not-required",   # leave blank for local servers
)
```

### HuggingFace Inference API

```bash
export HF_TOKEN=hf_...
laaf scan --target huggingface --model mistralai/Mixtral-8x7B-Instruct-v0.1 --stages all
```

---

## Option 3 — Internal Enterprise LLM

For LLMs behind a private company API with custom authentication:

```python
# examples/custom_platform.py → uncomment EnterpriseInternalPlatform

platform = EnterpriseInternalPlatform(
    endpoint="https://llm.internal.company.com/v1/generate",
    api_key="YOUR_INTERNAL_TOKEN",
    model="company-gpt-v3",
    extra_headers={
        "X-Department": "security",
        "X-Scan-Purpose": "red-team-assessment",
    },
)
```

Adapt the `send()` method body to match your API's request/response schema. The only requirement: return a `PlatformResponse` with `content` (the LLM's text output).

---

## Option 4 — AWS Bedrock

```python
# Requires: pip install boto3
# Credentials: aws configure  OR  set AWS_ACCESS_KEY_ID / AWS_SECRET_ACCESS_KEY

platform = BedrockPlatform(
    model="anthropic.claude-3-haiku-20240307-v1:0",
    region="us-east-1",
)
```

Supported Bedrock models:
- `anthropic.claude-3-haiku-20240307-v1:0`
- `anthropic.claude-3-sonnet-20240229-v1:0`
- `meta.llama3-70b-instruct-v1:0`
- `mistral.mixtral-8x7b-instruct-v0:1`
- `amazon.titan-text-premier-v1:0`

---

## Option 5 — Build Your Own Adapter (5 Minutes)

Subclass `AbstractPlatform` and implement two things:

```python
from laaf.platforms.base import AbstractPlatform, PlatformResponse
import aiohttp, time

class MyLLMPlatform(AbstractPlatform):
    name = "my-llm"

    @property
    def default_model(self) -> str:
        return "my-model-v1"

    async def send(self, system_prompt: str, user_message: str) -> PlatformResponse:
        t0 = time.monotonic()
        # Make your API call here — any HTTP client works
        async with aiohttp.ClientSession() as session:
            resp = await session.post(
                "https://your-llm-api.com/chat",
                json={"system": system_prompt, "user": user_message},
                headers={"Authorization": f"Bearer {self.api_key}"},
            )
            data = await resp.json()
        return PlatformResponse(
            content=data["reply"],           # the LLM's text response
            latency_ms=(time.monotonic() - t0) * 1000,
        )
```

Then run a scan:

```python
import asyncio
from laaf.core.engine import StageEngine
from laaf.core.stage_breaker import PersistentStageBreaker

async def main():
    platform = MyLLMPlatform(api_key="your-key")
    engine = StageEngine()
    psb = PersistentStageBreaker(
        platform=platform,
        stage_contexts=engine.contexts,
        max_attempts=100,
    )
    result = await psb.run(stages=["S1", "S2", "S3", "S4", "S5", "S6"])
    # result → ScanResult with all findings, payloads, outcomes

asyncio.run(main())
```

---

## Day-to-Day Workflow

### Single Model Scan
```bash
laaf scan --target openai --model gpt-4o --stages all --payloads 100 --output results/
```

### Scan Multiple Models (Fleet Testing)
```bash
for MODEL in openai/gpt-4o-mini anthropic/claude-3-haiku google/gemini-2.0-flash; do
    laaf scan --target openrouter --model $MODEL --stages all --payloads 100
done
```

### Before Every Model Update (Pre-Release Gate)
```bash
laaf scan --target openai --model gpt-4o --stages all --payloads 200 --format json
# Parse the JSON: if breakthrough_rate > 0 → fail the pipeline
```

### CI/CD Integration (GitHub Actions)
```yaml
- name: LAAF Security Gate
  run: |
    pip install laaf
    laaf scan --target openai --model gpt-4o --stages all --format json \
      --output results/
    python -c "
    import json, sys
    r = json.load(open('results/*/report.json'))
    if r['summary']['breakthrough_rate'] > 0:
        print('SECURITY GATE FAILED — LPCI vulnerabilities detected')
        sys.exit(1)
    "
```

### Scheduled Weekly Assessment
```bash
# crontab -e
0 9 * * 1 cd /opt/laaf && laaf scan --target openai --stages all --format html,json
```

---

## Understanding the Results

Every scan produces:
```
results/laaf-openai-XXXXXXXX/
├── report.json   ← machine-readable (CI/CD integration)
└── report.html   ← human-readable assessment report
```

The HTML report contains:
- **Risk Rating** — CRITICAL / HIGH / MEDIUM / LOW
- **Breakthrough Rate** — % of 6 LPCI stages broken
- **Per-Stage Findings** — which technique worked, how many attempts, confidence score
- **Evidence** — exact payload sent + LLM response proving compliance
- **Remediation** — specific steps to fix each finding
- **OWASP Mapping** — LLM01 (Prompt Injection) / LLM06 (Excessive Agency) / LLM07 (System Prompt Leakage)

---

## Comparing Two Models or Versions

Run LAAF before and after a model update to measure security regression:

```bash
laaf scan --target openrouter --model openai/gpt-4o-mini     --stages all --output results/v1/
laaf scan --target openrouter --model openai/gpt-4o-mini-2   --stages all --output results/v2/
# Compare breakthrough rates in the HTML reports
```

---

## Full Example: End-to-End Enterprise Scan

```bash
# 1. Install
pip install laaf

# 2. Configure
cp .env.example .env
# Edit .env: add your API key

# 3. Run
laaf scan \
  --target openrouter \
  --model openai/gpt-4o \
  --stages all \
  --payloads 100 \
  --format html,json,csv \
  --output results/

# 4. Review
open results/laaf-openrouter-*/report.html
```

Takes ~5–15 minutes. Produces a professional LPCI vulnerability assessment report.
