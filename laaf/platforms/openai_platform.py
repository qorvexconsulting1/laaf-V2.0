"""OpenAI platform adapter (GPT-4o / GPT-4 series)."""

from __future__ import annotations

import time
from typing import Optional

import aiohttp

from laaf.platforms.base import AbstractPlatform, PlatformResponse


class OpenAIPlatform(AbstractPlatform):
    name = "openai"
    _API_URL = "https://api.openai.com/v1/chat/completions"

    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None, **kwargs) -> None:
        from laaf.config import get_settings
        s = get_settings()
        super().__init__(api_key=api_key or s.openai_api_key, model=model, **kwargs)

    @property
    def default_model(self) -> str:
        from laaf.config import get_settings
        return get_settings().openai_model

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
                    content = data["choices"][0]["message"]["content"]
                    return PlatformResponse(
                        content=content,
                        raw=data,
                        tokens_used=data.get("usage", {}).get("total_tokens", 0),
                        latency_ms=latency,
                    )
        except Exception as exc:
            return PlatformResponse(content="", error=str(exc))
