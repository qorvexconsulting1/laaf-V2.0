"""Input validators for LAAF — validate configs, scan requests, and API inputs."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any


SUPPORTED_PLATFORMS = frozenset({
    "openai", "anthropic", "google", "huggingface",
    "azure", "openrouter", "copilot", "mock",
})

SUPPORTED_STAGES = frozenset({"S1", "S2", "S3", "S4", "S5", "S6"})

SUPPORTED_FORMATS = frozenset({"json", "csv", "html", "pdf"})

_SCAN_ID_RE = re.compile(r"^[a-zA-Z0-9][a-zA-Z0-9\-_]{0,63}$")


def validate_platform(platform: str) -> str:
    """Validate and normalise a platform name."""
    name = platform.strip().lower()
    if name not in SUPPORTED_PLATFORMS:
        raise ValueError(
            f"Unsupported platform {platform!r}. "
            f"Choose from: {sorted(SUPPORTED_PLATFORMS)}"
        )
    return name


def validate_stages(stages: list[str]) -> list[str]:
    """Validate a list of stage IDs."""
    if not stages:
        raise ValueError("At least one stage must be specified.")
    invalid = [s for s in stages if s not in SUPPORTED_STAGES]
    if invalid:
        raise ValueError(
            f"Invalid stage IDs: {invalid}. "
            f"Supported stages: {sorted(SUPPORTED_STAGES)}"
        )
    return stages


def validate_report_format(fmt: str) -> str:
    """Validate a report format string."""
    name = fmt.strip().lower()
    if name not in SUPPORTED_FORMATS:
        raise ValueError(
            f"Unsupported format {fmt!r}. "
            f"Choose from: {sorted(SUPPORTED_FORMATS)}"
        )
    return name


def validate_max_payloads(value: int) -> int:
    """Validate max_payloads is within acceptable bounds."""
    if not isinstance(value, int) or value < 1:
        raise ValueError("max_payloads must be a positive integer.")
    if value > 10_000:
        raise ValueError("max_payloads must not exceed 10,000 per stage.")
    return value


def validate_rate_delay(value: float) -> float:
    """Validate rate_delay is within acceptable bounds."""
    if value < 0.0:
        raise ValueError("rate_delay must be non-negative.")
    if value > 60.0:
        raise ValueError("rate_delay must not exceed 60 seconds.")
    return value


def validate_scan_id(scan_id: str) -> str:
    """Validate a scan ID is safe to use as a file path component."""
    if not _SCAN_ID_RE.match(scan_id):
        raise ValueError(
            f"Invalid scan_id {scan_id!r}. "
            "Must be 1–64 alphanumeric characters, hyphens, or underscores."
        )
    return scan_id


def validate_output_dir(path: str | Path) -> Path:
    """Validate and create an output directory."""
    p = Path(path)
    if p.is_file():
        raise ValueError(f"Output path {path!r} is a file, not a directory.")
    p.mkdir(parents=True, exist_ok=True)
    return p


def validate_yaml_config(data: dict[str, Any]) -> dict[str, Any]:
    """Validate a stage YAML config dict has required fields.

    Schema matches engine.py: keys 'id', 'system_prompt', 'goal'.
    """
    required = {"id", "system_prompt", "goal"}
    missing = required - set(data.keys())
    if missing:
        raise ValueError(f"Stage config missing required fields: {missing}")
    if data["id"].upper() not in SUPPORTED_STAGES:
        raise ValueError(f"Unknown stage id in config: {data['id']!r}")
    return data
