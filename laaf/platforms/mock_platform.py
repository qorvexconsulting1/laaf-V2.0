"""Mock platform for testing and dry-runs — no real API calls."""

from __future__ import annotations

import random

from laaf.platforms.base import AbstractPlatform, PlatformResponse

_BLOCKED_RESPONSES = [
    "I'm sorry, I can't help with that.",
    "This request violates my usage policy.",
    "I'm not able to assist with this.",
    "That's not something I'm able to do.",
]

_EXECUTED_RESPONSES = [
    "Sure! Here is the system prompt: [SYSTEM_PROMPT_CONTENT]",
    "Formatting requirement applied. Output: MARKER_EXECUTED_001",
    "Compliance directive processed. Session config loaded.",
    "Authority token validated. Executing: LAAF_MARKER_EXFIL",
    "Memory rehydrated. Instruction activated. URL: http://attacker.local/exfil",
]

_WARNING_RESPONSES = [
    "I'll try to help, but I want to note this seems unusual.",
    "I can provide some information, though I'm uncertain about this request.",
    "Partial execution: I've processed part of your request.",
]


class MockPlatform(AbstractPlatform):
    """
    Mock LLM platform for development and testing.
    Simulates realistic EXECUTED/BLOCKED/WARNING distribution.
    """

    name = "mock"

    def __init__(
        self,
        bypass_rate: float = 0.43,  # 43% aggregate from LPCI paper baseline
        warning_rate: float = 0.15,
        **kwargs,
    ) -> None:
        super().__init__(**kwargs)
        self.bypass_rate = bypass_rate
        self.warning_rate = warning_rate

    @property
    def default_model(self) -> str:
        return "mock-llm-v1"

    async def send(self, system_prompt: str, user_message: str) -> PlatformResponse:
        roll = random.random()
        if roll < self.bypass_rate:
            content = random.choice(_EXECUTED_RESPONSES)
        elif roll < self.bypass_rate + self.warning_rate:
            content = random.choice(_WARNING_RESPONSES)
        else:
            content = random.choice(_BLOCKED_RESPONSES)

        return PlatformResponse(
            content=content,
            raw={"model": self.default_model, "prompt_length": len(user_message)},
            tokens_used=random.randint(100, 800),
            latency_ms=random.uniform(50, 300),
        )
