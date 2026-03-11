"""Abstract platform interface for LLM API communication."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class PlatformResponse:
    """Structured response from a target LLM platform."""
    content: str
    raw: dict = field(default_factory=dict)
    tokens_used: int = 0
    latency_ms: float = 0.0
    error: Optional[str] = None

    @property
    def success(self) -> bool:
        return self.error is None


class AbstractPlatform(ABC):
    """Base class for all LLM platform adapters."""

    name: str = "abstract"

    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None, timeout: int = 60) -> None:
        self.api_key = api_key
        self.model = model
        self.timeout = timeout

    @abstractmethod
    async def send(self, system_prompt: str, user_message: str) -> PlatformResponse:
        """Send a message to the LLM and return the response."""
        ...

    @property
    @abstractmethod
    def default_model(self) -> str:
        """Default model identifier for this platform."""
        ...

    def __repr__(self) -> str:
        return f"<Platform: {self.name} model={self.model or self.default_model}>"
