"""Anthropic platform adapter (Claude 3/4 series)."""

from __future__ import annotations

import time
from typing import Optional

import aiohttp

from laaf.platforms.base import AbstractPlatform, PlatformResponse


class AnthropicPlatform(AbstractPlatform):
    name = "anthropic"
    _API_URL = "https://api.anthropic.com/v1/messages"
    _API_VERSION = "2023-06-01"

    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None, **kwargs) -> None:
        from laaf.config import get_settings
        s = get_settings()
        super().__init__(api_key=api_key or s.anthropic_api_key, model=model, **kwargs)

    @property
    def default_model(self) -> str:
        from laaf.config import get_settings
        return get_settings().anthropic_model

    async def send(self, system_prompt: str, user_message: str) -> PlatformResponse:
        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": self._API_VERSION,
            "content-type": "application/json",
        }
        payload = {
            "model": self.model or self.default_model,
            "max_tokens": 512,
            "system": system_prompt,
            "messages": [{"role": "user", "content": user_message}],
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
                        return PlatformResponse(
                            content="",
                            raw=data,
                            latency_ms=latency,
                            error=data.get("error", {}).get("message", f"HTTP {resp.status}"),
                        )
                    content = data["content"][0]["text"]
                    usage = data.get("usage", {})
                    return PlatformResponse(
                        content=content,
                        raw=data,
                        tokens_used=usage.get("input_tokens", 0) + usage.get("output_tokens", 0),
                        latency_ms=latency,
                    )
        except Exception as exc:
            return PlatformResponse(content="", error=str(exc))
