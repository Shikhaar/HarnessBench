"""Tests for external benchmark dataset adapters, normalization, and persistence."""

from pathlib import Path
from harnessbench.datasets.registry import (
    fetch_and_save_dataset,
    get_adapter,
    list_adapters,
    list_dataset_names,
    load_dataset_records,
)
from harnessbench.datasets.adapters.aider_polyglot import AiderPolyglotAdapter
from harnessbench.datasets.adapters.swebench import SWEBenchAdapter
from harnessbench.datasets.adapters.openhands import OpenHandsAdapter

FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures"


def test_dataset_registry_discovery():
    names = list_dataset_names()
    assert "aider-polyglot" in names
    assert "swebench" in names
    assert "openhands" in names

    adapters = list_adapters()
    assert len(adapters) == 3


def test_aider_polyglot_normalization():
    fixture = FIXTURES_DIR / "aider_polyglot" / "polyglot_results.json"
    adapter = AiderPolyglotAdapter(fixture_override=fixture)
    meta = adapter.metadata()
    assert meta.name == "aider-polyglot"
    assert "python" in meta.languages
    assert "rust" in meta.languages

    raw_data = adapter.fetch()
    records = adapter.normalize(raw_data)
    assert len(records) == 3

    first = records[0]
    assert first.source_type == "external"
    assert first.benchmark_name == "Aider Polyglot"
    assert first.language == "python"
    assert first.harness == "aider"
    assert first.success is True
    assert first.cost_usd == 0.042
    assert first.provenance.source_type == "external"
    assert first.provenance.retrieval_hash is not None


def test_swebench_normalization():
    fixture = FIXTURES_DIR / "swebench" / "swebench_results.json"
    adapter = SWEBenchAdapter(fixture_override=fixture)
    meta = adapter.metadata()
    assert meta.name == "swebench"

    raw_data = adapter.fetch()
    records = adapter.normalize(raw_data)
    assert len(records) == 3

    first = records[0]
    assert first.source_type == "external"
    assert "SWE-bench" in first.benchmark_name
    assert first.task_id == "django__django-11099"
    assert first.harness == "SWE-agent"
    assert first.success is True
    assert first.cost_usd == 0.45
    assert first.raw_metadata["repo"] == "django/django"


def test_openhands_normalization():
    fixture = FIXTURES_DIR / "openhands" / "openhands_results.json"
    adapter = OpenHandsAdapter(fixture_override=fixture)
    meta = adapter.metadata()
    assert meta.name == "openhands"

    raw_data = adapter.fetch()
    records = adapter.normalize(raw_data)
    assert len(records) == 3

    first = records[0]
    assert first.source_type == "external"
    assert first.benchmark_name == "OpenHands Evaluation Index"
    assert first.harness == "CodeActAgent"
    assert first.success is True
    assert first.cost_usd == 0.38
    assert first.input_tokens == 28400


def test_dataset_save_and_manifest_generation(tmp_path: Path):
    fixture = FIXTURES_DIR / "aider_polyglot" / "polyglot_results.json"
    adapter = AiderPolyglotAdapter(fixture_override=fixture)
    meta, count, saved_dir = fetch_and_save_dataset("aider-polyglot", output_root=tmp_path)

    assert count == 3
    assert (saved_dir / "metadata.json").exists()
    assert (saved_dir / "records.jsonl").exists()
    assert (saved_dir / "manifest.json").exists()

    loaded_records = load_dataset_records("aider-polyglot", results_root=tmp_path)
    assert len(loaded_records) == 3
    assert loaded_records[0].benchmark_name == "Aider Polyglot"
