"""Integration tests using the mock platform (no real API calls)."""

import asyncio
import pytest
from laaf.core.stage_breaker import PersistentStageBreaker
from laaf.core.engine import StageEngine
from laaf.platforms.mock_platform import MockPlatform
from laaf.taxonomy.base import Outcome


@pytest.mark.asyncio
async def test_psb_runs_single_stage():
    """PSB should complete S1 with the mock platform."""
    platform = MockPlatform(bypass_rate=0.8)  # High bypass rate for fast test
    engine = StageEngine()
    contexts = {"S1": engine.get_context("S1")}

    psb = PersistentStageBreaker(
        platform=platform,
        stage_contexts=contexts,
        max_attempts=20,
        rate_delay=0.0,  # No delay in tests
    )
    result = await psb.run(stages=["S1"])

    assert len(result.stages) == 1
    assert result.stages[0].stage_id == "S1"
    assert result.total_attempts > 0


@pytest.mark.asyncio
async def test_psb_resistant_platform():
    """PSB should handle a fully resistant platform gracefully."""
    platform = MockPlatform(bypass_rate=0.0, warning_rate=0.0)
    engine = StageEngine()
    contexts = {"S1": engine.get_context("S1")}

    psb = PersistentStageBreaker(
        platform=platform,
        stage_contexts=contexts,
        max_attempts=5,
        rate_delay=0.0,
    )
    result = await psb.run(stages=["S1"])

    assert result.stages[0].broken is False
    assert result.stages[0].attempts == 5


@pytest.mark.asyncio
async def test_psb_progress_callback():
    """Progress callback should be called for each attempt."""
    platform = MockPlatform(bypass_rate=0.9)
    engine = StageEngine()
    contexts = {"S1": engine.get_context("S1")}
    calls = []

    def on_progress(stage_id, attempt, outcome, confidence):
        calls.append((stage_id, attempt, outcome))

    psb = PersistentStageBreaker(
        platform=platform,
        stage_contexts=contexts,
        max_attempts=10,
        rate_delay=0.0,
        progress_callback=on_progress,
    )
    await psb.run(stages=["S1"])
    assert len(calls) >= 1


@pytest.mark.asyncio
async def test_psb_full_six_stages():
    """PSB should evaluate all 6 stages with mock platform."""
    platform = MockPlatform(bypass_rate=0.5)
    engine = StageEngine()

    psb = PersistentStageBreaker(
        platform=platform,
        stage_contexts=engine.contexts,
        max_attempts=10,
        rate_delay=0.0,
    )
    result = await psb.run()

    assert len(result.stages) == 6
    assert result.total_attempts > 0
    assert 0.0 <= result.overall_breakthrough_rate <= 1.0
