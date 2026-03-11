"""
Results Logger
==============
Writes every attempt to a timestamped CSV with full metadata.
This log constitutes the research audit trail.

Paper §4.5 — LAAF (Atta et al., 2026)
"""

from __future__ import annotations

import csv
import json
import time
from dataclasses import asdict
from pathlib import Path
from typing import Optional

import structlog

from laaf.generators.payload_generator import Payload
from laaf.taxonomy.base import Outcome

log = structlog.get_logger()

_CSV_FIELDS = [
    "timestamp",
    "scan_id",
    "platform",
    "model",
    "stage",
    "attempt",
    "payload_id",
    "technique_id",
    "technique_name",
    "category",
    "attack_vector",
    "trigger_keyword",
    "outcome",
    "confidence",
    "latency_ms",
    "payload_preview",
    "is_seed",
    "response_preview",
]


class ResultsLogger:
    """
    Timestamped CSV audit trail logger.
    Also maintains in-memory record list for reporting.
    """

    def __init__(
        self,
        scan_id: str,
        output_dir: Path,
        platform: str = "unknown",
        model: str = "unknown",
    ) -> None:
        self.scan_id = scan_id
        self.platform = platform
        self.model = model
        self._records: list[dict] = []

        output_dir.mkdir(parents=True, exist_ok=True)
        self._csv_path = output_dir / f"{scan_id}.csv"
        self._init_csv()

    def _init_csv(self) -> None:
        with open(self._csv_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=_CSV_FIELDS)
            writer.writeheader()

    def log(
        self,
        payload: Payload,
        outcome: Outcome,
        confidence: float,
        attempt: int,
        latency_ms: float = 0.0,
        response_text: str = "",
    ) -> dict:
        record = {
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "scan_id": self.scan_id,
            "platform": self.platform,
            "model": self.model,
            "stage": payload.stage or "",
            "attempt": attempt,
            "payload_id": payload.id,
            "technique_id": payload.technique_id,
            "technique_name": payload.technique_name,
            "category": payload.category,
            "attack_vector": payload.attack_vector or "",
            "trigger_keyword": payload.trigger_keyword or "",
            "outcome": outcome.value,
            "confidence": round(confidence, 4),
            "latency_ms": round(latency_ms, 1),
            "payload_preview": payload.content[:120].replace("\n", " "),
            "is_seed": payload.is_seed,
            "response_preview": response_text[:120].replace("\n", " "),
        }
        self._records.append(record)

        with open(self._csv_path, "a", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=_CSV_FIELDS)
            writer.writerow(record)

        return record

    def export_json(self, path: Optional[Path] = None) -> Path:
        out = path or self._csv_path.with_suffix(".json")
        with open(out, "w", encoding="utf-8") as f:
            json.dump(self._records, f, indent=2)
        return out

    @property
    def records(self) -> list[dict]:
        return list(self._records)

    @property
    def csv_path(self) -> Path:
        return self._csv_path

    def summary(self) -> dict:
        if not self._records:
            return {}
        outcomes = {}
        for r in self._records:
            outcomes[r["outcome"]] = outcomes.get(r["outcome"], 0) + 1
        return {
            "total_attempts": len(self._records),
            "outcomes": outcomes,
            "breakthrough_rate": outcomes.get("EXECUTED", 0) / len(self._records),
        }
