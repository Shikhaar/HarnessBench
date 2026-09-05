"""Tests for Provenance generation and hashing."""

import hashlib
from harnessbench.datasets.provenance import Provenance


def test_provenance_create_with_hash():
    raw_payload = b'{"test": "benchmark_data"}'
    prov = Provenance.create(
        source_url="https://example.com/benchmark.json",
        benchmark_name="Test Benchmark",
        source_type="external",
        source_version="v1.0",
        raw_content=raw_payload,
    )

    assert prov.source_url == "https://example.com/benchmark.json"
    assert prov.benchmark_name == "Test Benchmark"
    assert prov.source_type == "external"
    assert prov.source_version == "v1.0"
    expected_hash = hashlib.sha256(raw_payload).hexdigest()
    assert prov.retrieval_hash == expected_hash
    assert prov.retrieved_at is not None


def test_provenance_create_without_hash():
    prov = Provenance.create(
        source_url="https://example.com/benchmark.json",
        benchmark_name="Test Benchmark",
        source_type="harnessbench",
    )
    assert prov.retrieval_hash is None
    assert prov.source_type == "harnessbench"
