"""Shared pytest fixtures."""

import pytest
from laaf.platforms.mock_platform import MockPlatform
from laaf.generators.payload_generator import PayloadGenerator
from laaf.core.analyser import ResponseAnalyser
from laaf.core.engine import StageEngine


@pytest.fixture
def mock_platform():
    return MockPlatform(bypass_rate=0.5)


@pytest.fixture
def payload_generator():
    return PayloadGenerator(seed=42)


@pytest.fixture
def analyser():
    return ResponseAnalyser()


@pytest.fixture
def stage_engine():
    return StageEngine()
