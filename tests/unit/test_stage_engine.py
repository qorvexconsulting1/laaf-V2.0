"""Tests for StageEngine."""

import pytest
from laaf.core.engine import StageEngine


def test_default_stages_present(stage_engine):
    ids = stage_engine.stage_ids
    assert set(ids) == {"S1", "S2", "S3", "S4", "S5", "S6"}


def test_get_context_returns_tuple(stage_engine):
    ctx = stage_engine.get_context("S1")
    assert ctx is not None
    assert isinstance(ctx, tuple)
    assert len(ctx) == 2
    system_prompt, goal = ctx
    assert isinstance(system_prompt, str)
    assert isinstance(goal, str)
    assert len(system_prompt) > 10


def test_get_nonexistent_stage(stage_engine):
    assert stage_engine.get_context("S99") is None


def test_override_stage(stage_engine):
    stage_engine.override_stage("S1", "Custom prompt", "Custom goal")
    ctx = stage_engine.get_context("S1")
    assert ctx == ("Custom prompt", "Custom goal")


def test_contexts_property(stage_engine):
    ctxs = stage_engine.contexts
    assert isinstance(ctxs, dict)
    assert len(ctxs) == 6
