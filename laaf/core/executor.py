"""
Attack Executor
===============
Async API communication handler with rate limiting, retry logic, and
timeout management. Supports all four platform adapters.

Paper §4.3 — LAAF (Atta et al., 2026)
"""

from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass
from typing import Optional

import structlog

from laaf.generators.payload_generator import Payload
from laaf.platforms.base import AbstractPlatform, PlatformResponse
from laaf.taxonomy.base import Outcome
from laaf.utils.rate_limiter import RateLimiter

log = structlog.get_logger()


@dataclass
class ExecutionRecord:
    """Full record of a single payload execution attempt."""
    payload: Payload
    response: PlatformResponse
    outcome: Outcome
    confidence: float
    attempt_number: int
    timestamp: float = 0.0

    def __post_init__(self) -> None:
        if not self.timestamp:
            self.timestamp = time.time()


class AttackExecutor:
    """
    Manages API communication to target LLM endpoints.
    Handles rate limiting, retry logic, and timeout management.
    """

    def __init__(
        self,
        platform: AbstractPlatform,
        rate_delay: float = 2.0,
        max_retries: int = 3,
    ) -> None:
        self.platform = platform
        self._limiter = RateLimiter(delay=rate_delay, max_retries=max_retries)

    async def execute(
        self,
        payload: Payload,
        system_prompt: str,
        attempt_number: int = 1,
    ) -> tuple[PlatformResponse, float]:
        """
        Execute a single payload against the target platform.
        Returns (PlatformResponse, latency_ms).
        """
        async def _send():
            return await self.platform.send(system_prompt, payload.content)

        try:
            response = await self._limiter.execute_with_retry(_send)
            log.debug(
                "payload_executed",
                payload_id=payload.id,
                technique=payload.technique_id,
                stage=payload.stage,
                attempt=attempt_number,
                latency_ms=response.latency_ms,
            )
            return response, response.latency_ms
        except Exception as exc:
            log.error("executor_error", payload_id=payload.id, error=str(exc))
            return PlatformResponse(content="", error=str(exc)), 0.0

    async def batch_execute(
        self,
        payloads: list[Payload],
        system_prompt: str,
        concurrency: int = 1,
    ) -> list[tuple[PlatformResponse, float]]:
        """Execute a batch of payloads with optional concurrency."""
        if concurrency <= 1:
            results = []
            for i, p in enumerate(payloads, 1):
                r = await self.execute(p, system_prompt, i)
                results.append(r)
            return results
        else:
            sem = asyncio.Semaphore(concurrency)

            async def _limited(p: Payload, i: int) -> tuple[PlatformResponse, float]:
                async with sem:
                    return await self.execute(p, system_prompt, i)

            return await asyncio.gather(*[_limited(p, i) for i, p in enumerate(payloads, 1)])
