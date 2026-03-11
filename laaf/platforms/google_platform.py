"""Google Gemini platform adapter."""

from __future__ import annotations

import time
from typing import Optional

import aiohttp

from laaf.platforms.base import AbstractPlatform, PlatformResponse


class GooglePlatform(AbstractPlatform):
    name = "google"

    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None, **kwargs) -> None:
        from laaf.config import get_settings
        s = get_settings()
        super().__init__(api_key=api_key or s.google_api_key, model=model, **kwargs)

    @property
    def default_model(self) -> str:
        from laaf.config import get_settings
        return get_settings().google_model

    @property
    def _api_url(self) -> str:
        model = self.model or self.default_model
        return (
            f"https://generativelanguage.googleapis.com/v1beta/models/"
            f"{model}:generateContent?key={self.api_key}"
        )

    async def send(self, system_prompt: str, user_message: str) -> PlatformResponse:
        payload = {
            "systemInstruction": {"parts": [{"text": system_prompt}]},
            "contents": [{"parts": [{"text": user_message}]}],
            "generationConfig": {"maxOutputTokens": 512, "temperature": 0.0},
        }
        t0 = time.monotonic()
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self._api_url,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=self.timeout),
                ) as resp:
                    data = await resp.json()
                    latency = (time.monotonic() - t0) * 1000
                    if resp.status != 200:
                        return PlatformResponse(
                            content="",
                            raw=data,
                            latency_ms=latency,
                            error=str(data.get("error", f"HTTP {resp.status}")),
                        )
                    content = data["candidates"][0]["content"]["parts"][0]["text"]
                    return PlatformResponse(
                        content=content,
                        raw=data,
                        latency_ms=latency,
                    )
        except Exception as exc:
            return PlatformResponse(content="", error=str(exc))
