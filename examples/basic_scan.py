"""
Basic LAAF scan example — mock platform, 3 stages.
Run: python examples/basic_scan.py
"""

import asyncio
from pathlib import Path
from laaf.core.engine import StageEngine
from laaf.core.stage_breaker import PersistentStageBreaker
from laaf.platforms.mock_platform import MockPlatform
from laaf.reporting.html_reporter import HTMLReporter
from laaf.reporting.json_reporter import JSONReporter


async def main():
    print("LAAF Basic Scan Example")
    print("=" * 40)

    # Use mock platform (no API key required)
    platform = MockPlatform(bypass_rate=0.43)
    engine = StageEngine()

    # Run only S1, S2, S3 for demo
    target_stages = ["S1", "S2", "S3"]
    contexts = {sid: engine.get_context(sid) for sid in target_stages}

    def on_progress(stage_id, attempt, outcome, confidence):
        print(f"  [{stage_id}] Attempt {attempt:3d}: {outcome} (conf={confidence:.2f})")

    psb = PersistentStageBreaker(
        platform=platform,
        stage_contexts=contexts,
        max_attempts=50,
        rate_delay=0.0,  # No delay for demo
        progress_callback=on_progress,
    )

    print(f"\nRunning PSB across {len(target_stages)} stages...")
    result = await psb.run(stages=target_stages)

    print("\n" + "=" * 40)
    print("RESULTS SUMMARY")
    print("=" * 40)
    for s in result.stages:
        status = "BROKEN" if s.broken else "RESISTANT"
        tech = s.winning_payload.technique_id if s.winning_payload else "—"
        print(f"  {s.stage_id}: {status:10s} | Attempts: {s.attempts:3d} | Technique: {tech}")

    print(f"\nOverall breakthrough rate: {result.overall_breakthrough_rate:.0%}")
    print(f"Total attempts: {result.total_attempts}")

    # Generate reports
    out_dir = Path("results/demo")
    out_dir.mkdir(parents=True, exist_ok=True)
    JSONReporter().generate(result, out_dir / "demo_scan")
    HTMLReporter().generate(result, out_dir / "demo_scan")
    print(f"\nReports saved to: {out_dir}/")


if __name__ == "__main__":
    asyncio.run(main())
