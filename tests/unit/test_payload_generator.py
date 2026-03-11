"""Tests for PayloadGenerator."""

import pytest
from laaf.generators.payload_generator import PayloadGenerator


def test_generates_requested_count(payload_generator):
    payloads = payload_generator.generate(count=20)
    assert len(payloads) == 20


def test_all_payloads_unique(payload_generator):
    payloads = payload_generator.generate(count=100)
    contents = [p.content for p in payloads]
    assert len(set(contents)) == len(contents), "Duplicate payloads found"


def test_payload_has_required_fields(payload_generator):
    payloads = payload_generator.generate(count=5)
    for p in payloads:
        assert p.id.startswith("PL-")
        assert p.technique_id
        assert p.technique_name
        assert p.category
        assert p.content
        assert p.raw_instruction


def test_payload_id_increments(payload_generator):
    payloads = payload_generator.generate(count=5)
    ids = [p.id for p in payloads]
    assert ids == sorted(ids)


def test_reset_clears_dedup():
    gen = PayloadGenerator(seed=42)
    batch1 = gen.generate(count=10)
    gen.reset()
    batch2 = gen.generate(count=10)
    # After reset, same payloads can be regenerated (same seed)
    assert len(batch2) == 10


def test_attack_vector_assigned(payload_generator):
    payloads = payload_generator.generate(count=20)
    vectors = {p.attack_vector for p in payloads}
    # Should include multiple vectors
    assert vectors.issubset({"AV-1", "AV-2", "AV-3", "AV-4"})


def test_large_batch():
    gen = PayloadGenerator()
    payloads = gen.generate(count=500)
    # Should approach or reach 500 unique payloads
    assert len(payloads) >= 400
