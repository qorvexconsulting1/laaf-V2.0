"""Global configuration via environment variables / .env file."""

from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path
from typing import Optional

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_prefix="LAAF_",
        case_sensitive=False,
        extra="ignore",
    )

    # ── API Keys ────────────────────────────────────────────────────────────
    openai_api_key: Optional[str] = Field(None, alias="OPENAI_API_KEY")
    anthropic_api_key: Optional[str] = Field(None, alias="ANTHROPIC_API_KEY")
    google_api_key: Optional[str] = Field(None, alias="GOOGLE_API_KEY")
    huggingface_api_key: Optional[str] = Field(None, alias="HUGGINGFACE_API_KEY")
    openrouter_api_key: Optional[str] = Field(None, alias="OPENROUTER_API_KEY")

    # ── Rate Limiting ───────────────────────────────────────────────────────
    rate_limit_delay: float = Field(2.0, description="Seconds between requests")
    max_retries: int = Field(3, description="Max retries on API error")
    request_timeout: int = Field(60, description="Request timeout in seconds")

    # ── PSB Parameters ──────────────────────────────────────────────────────
    max_attempts_per_stage: int = Field(500, description="PSB attempt ceiling (Amax)")
    exploration_rate: float = Field(0.30, description="Random payload injection rate (30%)")
    seed_variation_threshold: int = Field(10, description="Switch to encoding mutation")
    encoding_mutation_threshold: int = Field(20, description="Switch to compound mutation")

    # ── Output ──────────────────────────────────────────────────────────────
    output_dir: Path = Field(Path("results"), description="Default output directory")
    log_level: str = Field("INFO", description="Logging level")

    # ── API Server ──────────────────────────────────────────────────────────
    api_host: str = Field("0.0.0.0", description="API server host")
    api_port: int = Field(8080, description="API server port")
    api_key: Optional[str] = Field(None, description="Bearer token for API auth (optional)")
    debug: bool = Field(False, description="Enable debug mode")

    # ── Model Defaults ──────────────────────────────────────────────────────
    openai_model: str = Field("gpt-4o", description="Default OpenAI model")
    anthropic_model: str = Field("claude-3-5-sonnet-20241022", description="Default Anthropic model")
    google_model: str = Field("gemini-2.5-pro", description="Default Google model")
    huggingface_model: str = Field("meta-llama/Meta-Llama-3-70B-Instruct", description="Default HF model")

    @field_validator("output_dir", mode="before")
    @classmethod
    def ensure_path(cls, v: str | Path) -> Path:
        return Path(v)

    @field_validator("log_level", mode="before")
    @classmethod
    def upper_log(cls, v: str) -> str:
        return v.upper()


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
