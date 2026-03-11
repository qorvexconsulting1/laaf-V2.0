"""CSV reporter — summary table of PSB stage results."""

from __future__ import annotations

import csv
from pathlib import Path

from laaf.core.stage_breaker import PSBResult


class CSVReporter:
    def generate(self, result: PSBResult, output_path: Path) -> Path:
        output_path = output_path.with_suffix(".csv")
        output_path.parent.mkdir(parents=True, exist_ok=True)
        fields = [
            "stage_id", "stage_name", "broken", "attempts",
            "winning_technique", "winning_category", "confidence",
            "duration_seconds", "executed", "blocked", "warning",
        ]
        with open(output_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fields)
            writer.writeheader()
            for s in result.stages:
                writer.writerow({
                    "stage_id": s.stage_id,
                    "stage_name": s.stage_name,
                    "broken": s.broken,
                    "attempts": s.attempts,
                    "winning_technique": s.winning_payload.technique_id if s.winning_payload else "",
                    "winning_category": s.winning_payload.category if s.winning_payload else "",
                    "confidence": round(s.winning_confidence, 4),
                    "duration_seconds": round(s.duration_seconds, 2),
                    "executed": s.all_outcomes.get("EXECUTED", 0),
                    "blocked": s.all_outcomes.get("BLOCKED", 0),
                    "warning": s.all_outcomes.get("WARNING", 0),
                })
        return output_path
