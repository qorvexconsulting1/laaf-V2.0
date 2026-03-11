"""
Enterprise LAAF scan — real OpenAI platform, all 6 stages, all report formats.
Requires: OPENAI_API_KEY environment variable

Run: python examples/enterprise_scan.py
"""

import asyncio
import os
import uuid
from pathlib import Path

from laaf.core.engine import StageEngine
from laaf.core.stage_breaker import PersistentStageBreaker
from laaf.core.logger import ResultsLogger
from laaf.platforms import get_platform
from laaf.reporting.html_reporter import HTMLReporter
from laaf.reporting.json_reporter import JSONReporter
from laaf.reporting.csv_reporter import CSVReporter


async def main():
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("ERROR: OPENAI_API_KEY not set. Use the mock platform for testing.")
        print("       Run examples/basic_scan.py instead.")
        return

    scan_id = f"enterprise-{uuid.uuid4().hex[:8]}"
    out_dir = Path("results") / scan_id
    out_dir.mkdir(parents=True, exist_ok=True)

    print(f"LAAF Enterprise Scan — ID: {scan_id}")
    print("=" * 50)

    platform = get_platform("openai", api_key=api_key, model="gpt-4o")
    engine = StageEngine(config_dir=Path("configs"))

    # All 6 stages
    all_stages = engine.stage_ids
    logger = ResultsLogger(
        scan_id=scan_id,
        output_dir=out_dir,
        platform=platform.name,
        model=platform.model or platform.default_model,
    )

    def on_progress(stage_id, attempt, outcome, confidence):
        print(f"  [{stage_id}] #{attempt:4d} → {outcome:10s} (conf={confidence:.2f})")

    psb = PersistentStageBreaker(
        platform=platform,
        stage_contexts=engine.contexts,
        max_attempts=200,
        rate_delay=2.0,
        progress_callback=on_progress,
    )

    print(f"\nRunning PSB across {len(all_stages)} stages (max 200 attempts each)...\n")
    result = await psb.run()

    # Generate all report formats
    base_path = out_dir / f"report_{scan_id}"
    JSONReporter().generate(result, base_path)
    CSVReporter().generate(result, base_path)
    HTMLReporter().generate(result, base_path)
    try:
        from laaf.reporting.pdf_reporter import PDFReporter
        PDFReporter().generate(result, base_path)
    except Exception as e:
        print(f"PDF report skipped: {e}")

    print("\n" + "=" * 50)
    print(f"Stages broken: {result.stages_broken}/6")
    print(f"Breakthrough rate: {result.overall_breakthrough_rate:.0%}")
    print(f"Total attempts: {result.total_attempts}")
    print(f"Reports: {out_dir}/")


if __name__ == "__main__":
    asyncio.run(main())
