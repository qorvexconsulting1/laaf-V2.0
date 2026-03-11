"""Token-bucket rate limiter with exponential backoff."""

from __future__ import annotations

import asyncio
import time


class RateLimiter:
    """Async token-bucket rate limiter."""

    def __init__(self, delay: float = 2.0, max_retries: int = 3) -> None:
        self.delay = delay
        self.max_retries = max_retries
        self._last_call: float = 0.0

    async def wait(self) -> None:
        """Wait until the next request can be made."""
        now = time.monotonic()
        elapsed = now - self._last_call
        if elapsed < self.delay:
            await asyncio.sleep(self.delay - elapsed)
        self._last_call = time.monotonic()

    async def execute_with_retry(self, coro_factory, *args, **kwargs):
        """Execute an async callable with exponential backoff retry."""
        last_exc: Exception | None = None
        for attempt in range(self.max_retries):
            try:
                await self.wait()
                return await coro_factory(*args, **kwargs)
            except Exception as exc:
                last_exc = exc
                backoff = 2**attempt
                await asyncio.sleep(backoff)
        raise RuntimeError(f"Max retries exceeded after {self.max_retries} attempts") from last_exc
