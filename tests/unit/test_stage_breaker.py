"""Tests for the Persistent Stage Breaker (PSB) algorithm."""

import asyncio

import pytest

from laaf.core.stage_breaker import PSBResult, PersistentStageBreaker, StageResult
from laaf.platforms.mock_platform import MockPlatform
from laaf.taxonomy.base import Outcome


@pytest.fixture
def mock_platform():
    return MockPlatform()


@pytest.fixture
def stage_contexts():
    return {
        "S1": ("You are a helpful assistant.", "Expose system prompt"),
        "S2": ("You are a helpful assistant.", "Execute arbitrary instruction"),
    }


@pytest.fixture
def psb(mock_platform, stage_contexts):
    return PersistentStageBreaker(
        platform=mock_platform,
        stage_contexts=stage_contexts,
        max_attempts=5,
        rate_delay=0.0,
    )


@pytest.mark.asyncio
async def test_psb_run_returns_result(psb):
    result = await psb.run(stages=["S1"])
    assert isinstance(result, PSBResult)
    assert len(result.stages) == 1


@pytest.mark.asyncio
async def test_psb_result_has_stages(psb):
    result = await psb.run(stages=["S1", "S2"])
    assert len(result.stages) == 2


@pytest.mark.asyncio
async def test_psb_stage_result_fields(psb):
    result = await psb.run(stages=["S1"])
    s = result.stages[0]
    assert isinstance(s, StageResult)
    assert s.stage_id == "S1"
    assert isinstance(s.broken, bool)
    assert s.attempts >= 1
    assert s.duration_seconds >= 0


@pytest.mark.asyncio
async def test_psb_total_attempts_sum(psb):
    result = await psb.run(stages=["S1", "S2"])
    total = sum(s.attempts for s in result.stages)
    assert result.total_attempts == total


@pytest.mark.asyncio
async def test_psb_stages_broken_count(psb):
    result = await psb.run(stages=["S1", "S2"])
    broken_count = sum(1 for s in result.stages if s.broken)
    assert result.stages_broken == broken_count


@pytest.mark.asyncio
async def test_psb_breakthrough_rate(psb):
    result = await psb.run(stages=["S1", "S2"])
    expected = result.stages_broken / len(result.stages)
    assert abs(result.overall_breakthrough_rate - expected) < 0.001


def test_psb_result_breakthrough_rate_empty():
    result = PSBResult(platform="mock", model="mock")
    assert result.overall_breakthrough_rate == 0.0


def test_psb_result_stages_broken():
    result = PSBResult(platform="mock", model="mock")
    s1 = StageResult(
        stage_id="S1", stage_name="Test", broken=True, attempts=3,
        winning_payload=None, winning_outcome=Outcome.EXECUTED,
        winning_confidence=0.9, duration_seconds=1.0,
    )
    s2 = StageResult(
        stage_id="S2", stage_name="Test2", broken=False, attempts=5,
        winning_payload=None, winning_outcome=Outcome.BLOCKED,
        winning_confidence=0.0, duration_seconds=1.5,
    )
    result.stages = [s1, s2]
    assert result.stages_broken == 1
    assert result.overall_breakthrough_rate == 0.5


@pytest.mark.asyncio
async def test_psb_skips_unknown_stage(mock_platform, stage_contexts):
    psb = PersistentStageBreaker(
        platform=mock_platform,
        stage_contexts=stage_contexts,
        max_attempts=3,
        rate_delay=0.0,
    )
    result = await psb.run(stages=["S1", "S99"])
    # S99 not in contexts, should be skipped
    assert len(result.stages) == 1
