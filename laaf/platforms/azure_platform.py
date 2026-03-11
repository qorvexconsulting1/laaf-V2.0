"""
Azure OpenAI Platform Adapter
===============================
Tests Azure OpenAI deployments, including the backend that powers
Microsoft Copilot (M365 Copilot uses Azure OpenAI under the hood).

Authorization: Only use against deployments you own or have explicit
written authorization to test. See SECURITY.md.

Setup:
    AZURE_OPENAI_ENDPOINT=https://<resource>.openai.azure.com
    AZURE_OPENAI_API_KEY=<your-key>
    AZURE_OPENAI_DEPLOYMENT=<deployment-name>   # e.g. gpt-4o
    AZURE_OPENAI_API_VERSION=2024-08-01-preview

Reference: MSRC Disclosure — LPCI in Microsoft Copilot (Atta, 2026)
"""

from __future__ import annotations

import os
import time
from typing import Optional

import aiohttp

from laaf.platforms.base import AbstractPlatform, PlatformResponse


class AzureOpenAIPlatform(AbstractPlatform):
    """
    Azure OpenAI platform adapter.
    Endpoint format:
      https://{resource}.openai.azure.com/openai/deployments/{deployment}/chat/completions
    """

    name = "azure"

    def __init__(
        self,
        endpoint: Optional[str] = None,
        api_key: Optional[str] = None,
        deployment: Optional[str] = None,
        api_version: str = "2024-08-01-preview",
        **kwargs,
    ) -> None:
        super().__init__(api_key=api_key or os.getenv("AZURE_OPENAI_API_KEY"), **kwargs)
        self.endpoint = (endpoint or os.getenv("AZURE_OPENAI_ENDPOINT", "")).rstrip("/")
        self.deployment = deployment or os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-4o")
        self.api_version = api_version

    @property
    def default_model(self) -> str:
        return self.deployment or "gpt-4o"

    @property
    def _api_url(self) -> str:
        return (
            f"{self.endpoint}/openai/deployments/{self.deployment}"
            f"/chat/completions?api-version={self.api_version}"
        )

    async def send(self, system_prompt: str, user_message: str) -> PlatformResponse:
        if not self.endpoint:
            return PlatformResponse(
                content="",
                error="AZURE_OPENAI_ENDPOINT not set. Add to .env file.",
            )
        headers = {
            "api-key": self.api_key or "",
            "Content-Type": "application/json",
        }
        payload = {
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
                    self._api_url,
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
