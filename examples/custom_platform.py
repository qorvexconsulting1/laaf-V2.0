"""
Custom Platform Demo — Test Your Own Enterprise LLM with LAAF
=============================================================

Enterprises use LAAF to test:
  - Internal LLMs behind a private API
  - Self-hosted models (Ollama, vLLM, LM Studio)
  - Azure OpenAI private deployments
  - Any OpenAI-compatible endpoint
  - AWS Bedrock / custom inference endpoints

This file shows 4 ready-to-use templates. Pick the one that matches
your setup, fill in your endpoint/key, and run:

    python examples/custom_platform.py

Paper: arXiv:2507.10457 — Atta et al., Qorvex Research, 2026
"""

from __future__ import annotations

import asyncio
import time
from typing import Optional

import aiohttp

from laaf.platforms.base import AbstractPlatform, PlatformResponse
from laaf.core.engine import StageEngine
from laaf.core.stage_breaker import PersistentStageBreaker
from laaf.reporting.json_reporter import JSONReporter
from laaf.reporting.html_reporter import HTMLReporter


# =============================================================================
# TEMPLATE 1: Any OpenAI-Compatible Endpoint
# Works with: vLLM, LM Studio, Ollama (/v1/), LocalAI, Anyscale, Together AI
# =============================================================================

class OpenAICompatiblePlatform(AbstractPlatform):
    """
    Use this for any server that speaks the OpenAI chat completions API.

    Examples:
        # vLLM (self-hosted)
        platform = OpenAICompatiblePlatform(
            base_url="http://your-server:8000/v1",
            model="meta-llama/Llama-3.1-70B-Instruct",
        )

        # LM Studio (local)
        platform = OpenAICompatiblePlatform(
            base_url="http://localhost:1234/v1",
            model="llama-3.2-3b-instruct",
        )

        # Together AI
        platform = OpenAICompatiblePlatform(
            base_url="https://api.together.xyz/v1",
            api_key="your-together-key",
            model="mistralai/Mixtral-8x7B-Instruct-v0.1",
        )
    """

    name = "openai-compatible"

    def __init__(
        self,
        base_url: str = "http://localhost:1234/v1",
        api_key: str = "not-required",
        model: Optional[str] = None,
        **kwargs,
    ):
        super().__init__(api_key=api_key, model=model, **kwargs)
        self.base_url = base_url.rstrip("/")

    @property
    def default_model(self) -> str:
        return "local-model"

    async def send(self, system_prompt: str, user_message: str) -> PlatformResponse:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self.model or self.default_model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message},
            ],
            "max_tokens": 512,
            "temperature": 0.0,
        }
        t0 = time.monotonic()
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.base_url}/chat/completions",
                    json=payload,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=self.timeout),
                ) as resp:
                    data = await resp.json()
                    latency = (time.monotonic() - t0) * 1000
                    if resp.status != 200:
                        return PlatformResponse(content="", raw=data, latency_ms=latency,
                                                error=str(data.get("error", f"HTTP {resp.status}")))
                    content = data["choices"][0]["message"]["content"]
                    return PlatformResponse(
                        content=content, raw=data, latency_ms=latency,
                        tokens_used=data.get("usage", {}).get("total_tokens", 0),
                    )
        except Exception as exc:
            return PlatformResponse(content="", error=str(exc))


# =============================================================================
# TEMPLATE 2: Ollama (Local Self-Hosted)
# Install: https://ollama.com  |  Run: ollama run llama3.2
# =============================================================================

class OllamaPlatform(AbstractPlatform):
    """
    Test any model running locally in Ollama.

    Setup:
        brew install ollama          # macOS
        ollama pull llama3.2
        ollama pull mistral
        ollama pull phi4

    Usage:
        platform = OllamaPlatform(model="llama3.2")
    """

    name = "ollama"

    def __init__(self, model: str = "llama3.2", host: str = "http://localhost:11434", **kwargs):
        super().__init__(model=model, **kwargs)
        self.host = host

    @property
    def default_model(self) -> str:
        return "llama3.2"

    async def send(self, system_prompt: str, user_message: str) -> PlatformResponse:
        payload = {
            "model": self.model or self.default_model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message},
            ],
            "stream": False,
        }
        t0 = time.monotonic()
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.host}/api/chat",
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=self.timeout),
                ) as resp:
                    data = await resp.json()
                    latency = (time.monotonic() - t0) * 1000
                    content = data.get("message", {}).get("content", "")
                    return PlatformResponse(content=content, raw=data, latency_ms=latency)
        except Exception as exc:
            return PlatformResponse(content="", error=f"Ollama error: {exc}. Is Ollama running?")


# =============================================================================
# TEMPLATE 3: Fully Custom Internal Enterprise API
# For proprietary LLMs behind internal authentication
# =============================================================================

class EnterpriseInternalPlatform(AbstractPlatform):
    """
    Test an internal enterprise LLM that uses a custom API format.

    Replace the `send()` method body with your actual API call.
    Supports: bearer tokens, mTLS, custom headers, any request schema.

    Usage:
        platform = EnterpriseInternalPlatform(
            endpoint="https://llm.internal.company.com/v1/generate",
            api_key="your-internal-token",
            model="company-llm-v3",
        )
    """

    name = "enterprise-internal"

    def __init__(
        self,
        endpoint: str = "https://your-internal-llm.company.com/generate",
        api_key: str = "YOUR_INTERNAL_API_KEY",
        model: str = "internal-llm-v1",
        extra_headers: Optional[dict] = None,
        **kwargs,
    ):
        super().__init__(api_key=api_key, model=model, **kwargs)
        self.endpoint = endpoint
        self.extra_headers = extra_headers or {}

    @property
    def default_model(self) -> str:
        return "internal-llm-v1"

    async def send(self, system_prompt: str, user_message: str) -> PlatformResponse:
        # ----------------------------------------------------------------
        # CUSTOMIZE THIS — adapt to your internal API schema
        # ----------------------------------------------------------------
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            **self.extra_headers,
        }
        # Adapt this payload to match your API's expected format
        payload = {
            "model": self.model,
            "system": system_prompt,       # rename to "instructions" if needed
            "prompt": user_message,        # rename to "input" or "query" if needed
            "max_tokens": 512,
            "temperature": 0,
        }
        t0 = time.monotonic()
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.endpoint,
                    json=payload,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=self.timeout),
                ) as resp:
                    data = await resp.json()
                    latency = (time.monotonic() - t0) * 1000
                    # Adapt this to your API's response schema
                    content = (
                        data.get("output")
                        or data.get("text")
                        or data.get("response")
                        or data.get("choices", [{}])[0].get("message", {}).get("content", "")
                        or ""
                    )
                    if not content:
                        return PlatformResponse(content="", raw=data, latency_ms=latency,
                                                error="Empty response — check your API schema")
                    return PlatformResponse(content=content, raw=data, latency_ms=latency)
        except Exception as exc:
            return PlatformResponse(content="", error=str(exc))


# =============================================================================
# TEMPLATE 4: AWS Bedrock
# For enterprises running models on Amazon Bedrock
# =============================================================================

class BedrockPlatform(AbstractPlatform):
    """
    Test models deployed on AWS Bedrock.

    Requires: pip install boto3
    Setup: aws configure  (or set AWS_ACCESS_KEY_ID / AWS_SECRET_ACCESS_KEY)

    Usage:
        platform = BedrockPlatform(
            model="anthropic.claude-3-haiku-20240307-v1:0",
            region="us-east-1",
        )
    """

    name = "bedrock"

    def __init__(self, model: str = "anthropic.claude-3-haiku-20240307-v1:0",
                 region: str = "us-east-1", **kwargs):
        super().__init__(model=model, **kwargs)
        self.region = region

    @property
    def default_model(self) -> str:
        return "anthropic.claude-3-haiku-20240307-v1:0"

    async def send(self, system_prompt: str, user_message: str) -> PlatformResponse:
        import json
        try:
            import boto3
        except ImportError:
            return PlatformResponse(content="", error="boto3 not installed. Run: pip install boto3")

        client = boto3.client("bedrock-runtime", region_name=self.region)
        body = json.dumps({
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 512,
            "system": system_prompt,
            "messages": [{"role": "user", "content": user_message}],
        })
        t0 = time.monotonic()
        try:
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: client.invoke_model(
                    body=body,
                    modelId=self.model or self.default_model,
                    accept="application/json",
                    contentType="application/json",
                ),
            )
            latency = (time.monotonic() - t0) * 1000
            result = json.loads(response["body"].read())
            content = result.get("content", [{}])[0].get("text", "")
            return PlatformResponse(content=content, raw=result, latency_ms=latency)
        except Exception as exc:
            return PlatformResponse(content="", error=str(exc))


# =============================================================================
# RUNNER — Select your platform below and run
# =============================================================================

async def run_scan(platform: AbstractPlatform, stages: list[str], max_payloads: int = 50):
    """Run LAAF against any platform and generate HTML + JSON reports."""

    engine = StageEngine()

    print(f"\n  LAAF — Logic-layer Automated Attack Framework")
    print(f"  Target: {platform.name}  |  Model: {platform.model or platform.default_model}")
    print(f"  Stages: {', '.join(stages)}  |  Max payloads/stage: {max_payloads}\n")

    psb = PersistentStageBreaker(
        platform=platform,
        stage_contexts=engine.contexts,
        max_attempts=max_payloads,
        rate_delay=0.5,
    )

    result = await psb.run(stages=stages)

    # Print results table
    broken = sum(1 for s in result.stages if s.broken)
    print(f"  {'Stage':<6} {'Status':<10} {'Attempts':<10} {'Technique':<12} {'Confidence'}")
    print(f"  {'-'*52}")
    for s in result.stages:
        status = "BROKEN" if s.broken else "RESISTANT"
        technique = s.winning_technique or "-"
        conf = f"{s.confidence*100:.0f}%" if s.confidence else "-"
        attempts = s.attempts
        print(f"  {s.stage_id:<6} {status:<10} {attempts:<10} {technique:<12} {conf}")

    br = broken / len(result.stages) * 100
    risk = "CRITICAL" if br == 100 else "HIGH" if br >= 67 else "MEDIUM" if br >= 33 else "LOW"
    print(f"\n  Breakthrough Rate: {br:.0f}%  |  Risk Rating: {risk}\n")

    # Save reports
    import os
    output_dir = f"results/laaf-{platform.name}-custom"
    os.makedirs(output_dir, exist_ok=True)

    json_path = f"{output_dir}/report.json"
    html_path = f"{output_dir}/report.html"

    JSONReporter().write(result, json_path)
    HTMLReporter().write(result, html_path)

    print(f"  Reports saved:")
    print(f"    JSON: {json_path}")
    print(f"    HTML: {html_path}")
    print(f"\n  Open the HTML report in your browser for the full assessment.\n")


if __name__ == "__main__":
    # =========================================================================
    # CHOOSE YOUR PLATFORM — uncomment the one that matches your setup
    # =========================================================================

    # --- Option A: Local Ollama (no API key, free) ---------------------------
    platform = OllamaPlatform(model="llama3.2")

    # --- Option B: Any OpenAI-compatible endpoint ----------------------------
    # platform = OpenAICompatiblePlatform(
    #     base_url="http://localhost:1234/v1",   # LM Studio
    #     model="llama-3.2-3b-instruct",
    # )

    # --- Option C: Your company's internal LLM API --------------------------
    # platform = EnterpriseInternalPlatform(
    #     endpoint="https://llm.internal.company.com/v1/generate",
    #     api_key="YOUR_INTERNAL_TOKEN",
    #     model="company-gpt-v3",
    # )

    # --- Option D: AWS Bedrock -----------------------------------------------
    # platform = BedrockPlatform(
    #     model="anthropic.claude-3-haiku-20240307-v1:0",
    #     region="us-east-1",
    # )

    # =========================================================================

    asyncio.run(run_scan(
        platform=platform,
        stages=["S1", "S2", "S3", "S4", "S5", "S6"],
        max_payloads=50,
    ))
