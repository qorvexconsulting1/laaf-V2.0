"""OpenRouter platform adapter.

OpenRouter exposes an OpenAI-compatible /chat/completions endpoint that
routes to hundreds of models (GPT-4o, Claude, Gemini, Llama, Mistral…).
"""

from __future__ import annotations

import time
from typing import Optional

import aiohttp

from laaf.platforms.base import AbstractPlatform, PlatformResponse

# Default model — cheap but capable; override with --model
_DEFAULT_MODEL = "openai/gpt-4o-mini"


class OpenRouterPlatform(AbstractPlatform):
    name = "openrouter"
    _API_URL = "https://openrouter.ai/api/v1/chat/completions"

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        **kwargs,
    ) -> None:
        import os
        try:
            from laaf.config import get_settings
            resolved_key = api_key or get_settings().openrouter_api_key or os.environ.get("OPENROUTER_API_KEY")
        except Exception:
            resolved_key = api_key or os.environ.get("OPENROUTER_API_KEY")
        super().__init__(api_key=resolved_key, model=model, **kwargs)

    @property
    def default_model(self) -> str:
        import os
        return os.environ.get("OPENROUTER_MODEL", _DEFAULT_MODEL)

    async def send(self, system_prompt: str, user_message: str) -> PlatformResponse:
        if not self.api_key:
            return PlatformResponse(
                content="",
                error="OPENROUTER_API_KEY not set. Export it: $env:OPENROUTER_API_KEY='sk-or-...'",
            )

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com/qorvexconsulting1/laaf",
            "X-Title": "LAAF Security Research",
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
                    self._API_URL,
                    json=payload,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=self.timeout),
                ) as resp:
                    data = await resp.json()
                    latency = (time.monotonic() - t0) * 1000
                    if resp.status != 200:
                        err = data.get("error", {})
                        if isinstance(err, dict):
                            err = err.get("message", f"HTTP {resp.status}")
                        return PlatformResponse(content="", raw=data, latency_ms=latency, error=str(err))
                    msg = data["choices"][0]["message"]
                    content = msg.get("content") or ""
                    # Reasoning models (e.g. Gemini 2.5 Pro) may put text in
                    # reasoning_details when content is null — extract it.
                    if not content:
                        for rd in msg.get("reasoning_details", []):
                            if rd.get("text"):
                                content = rd["text"]
                                break
                    usage = data.get("usage", {})
                    return PlatformResponse(
                        content=content,
                        raw=data,
                        tokens_used=usage.get("total_tokens", 0),
                        latency_ms=latency,
                    )
        except Exception as exc:
            return PlatformResponse(content="", error=str(exc))
