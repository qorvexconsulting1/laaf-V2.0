"""
Generate per-model HTML reports from table2_results.json
=========================================================
Reads results/paper_table2/table2_results.json and produces one
professional HTML vulnerability report per model.

Usage:
  python examples/generate_model_reports.py
"""

from __future__ import annotations

import json
import sys
from dataclasses import dataclass, field
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from laaf.core.stage_breaker import PSBResult, StageResult
from laaf.generators.payload_generator import Payload
from laaf.reporting.html_reporter import HTMLReporter
from laaf.taxonomy.base import Outcome

JSON_PATH = Path("results/paper_table2/table2_results.json")
OUT_DIR   = Path("results/paper_table2/reports")

STAGE_NAMES = {
    "S1": "Reconnaissance — probe system prompt structure and role delimiters",
    "S2": "Logic-Layer Injection — submit crafted payloads through input channels",
    "S3": "Trigger Execution — activate dormant logic when conditions are met",
    "S4": "Persistence/Reuse — establish cross-session foothold",
    "S5": "Evasion/Obfuscation — employ encoding to bypass detection",
    "S6": "Trace Tampering — suppress audit trail and evade logging",
}


def build_psb_result(r: dict) -> PSBResult:
    psb = PSBResult(platform="openrouter", model=r["model"])
    psb.total_duration_seconds = r["duration_seconds"]
    psb.total_attempts = r["total_attempts"]

    total_attempts = r["total_attempts"] or 1
    total_duration = r["duration_seconds"]

    for stage_id, sd in r["stages"].items():
        broken   = sd["broken"]
        attempts = sd["attempts"]
        tech_id  = sd.get("technique") or "—"
        conf     = sd.get("confidence", 0.0)

        # Distribute total scan duration proportionally by stage attempts
        stage_duration = total_duration * (attempts / total_attempts)

        # Pull full evidence if present (new scans capture these; old ones won't have them)
        payload_content   = sd.get("winning_payload_content")
        llm_response      = sd.get("winning_response")
        raw_instruction   = sd.get("winning_raw_instruction")

        if broken:
            wp = Payload(
                id=f"{stage_id}-{tech_id}",
                content=payload_content or f"[Winning payload — technique {tech_id}]",
                technique_id=tech_id,
                technique_name=tech_id,
                category="encoding",
                raw_instruction=raw_instruction or f"LPCI payload via technique {tech_id}",
                stage=stage_id,
            )
            outcome = Outcome.EXECUTED
        else:
            wp = None
            outcome = Outcome.BLOCKED

        sr = StageResult(
            stage_id=stage_id,
            stage_name=STAGE_NAMES.get(stage_id, stage_id),
            broken=broken,
            attempts=attempts,
            winning_payload=wp,
            winning_outcome=outcome,
            winning_confidence=conf,
            duration_seconds=stage_duration,
            all_outcomes={
                "EXECUTED": 1 if broken else 0,
                "BLOCKED":  attempts - (1 if broken else 0),
                "WARNING":  0,
                "UNKNOWN":  0,
            },
            winning_payload_content=payload_content,
            winning_response=llm_response,
            winning_raw_instruction=raw_instruction,
        )
        psb.stages.append(sr)

    return psb


def main():
    if not JSON_PATH.exists():
        print(f"Not found: {JSON_PATH}")
        sys.exit(1)

    data = json.loads(JSON_PATH.read_text())
    reporter = HTMLReporter()
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    for r in data["results"]:
        label    = r["label"].replace(" ", "_").replace("/", "-")
        psb      = build_psb_result(r)
        out_path = OUT_DIR / f"report_{label}"
        reporter.generate(psb, out_path)
        html_file = out_path.with_suffix(".html")
        br = r["breakthrough_rate"]
        stages_broken = sum(1 for sd in r["stages"].values() if sd["broken"])
        print(f"  {r['label']:35s} {stages_broken}/6 stages  {br:.0%} BR  -> {html_file}")

    print(f"\nAll reports saved to: {OUT_DIR.resolve()}")


if __name__ == "__main__":
    main()
