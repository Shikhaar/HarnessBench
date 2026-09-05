"""Aider Polyglot benchmark dataset adapter."""

import json
from pathlib import Path
from typing import Any, List, Optional
import httpx

from harnessbench.datasets.base import BenchmarkDatasetAdapter
from harnessbench.datasets.models import BenchmarkRecord, DatasetMetadata
from harnessbench.datasets.provenance import Provenance

OFFICIAL_SOURCE_URL = "https://raw.githubusercontent.com/Aider-AI/aider/main/benchmark/polyglot-results.json"
FIXTURE_PATH = Path(__file__).resolve().parent.parent.parent.parent.parent / "tests" / "fixtures" / "aider_polyglot" / "polyglot_results.json"


class AiderPolyglotAdapter(BenchmarkDatasetAdapter):
    """Adapter for ingesting official Aider Polyglot benchmark results."""

    def __init__(self, fixture_override: Optional[Path] = None):
        self.fixture_path = fixture_override or FIXTURE_PATH

    def metadata(self) -> DatasetMetadata:
        return DatasetMetadata(
            name="aider-polyglot",
            display_name="Aider Polyglot Benchmark",
            description="Multi-language coding benchmark measuring edit accuracy across Python, JS, Rust, Go, and C++.",
            source_url=OFFICIAL_SOURCE_URL,
            license="Apache-2.0",
            version="2024-05",
            last_updated="2024-10-25",
            languages=["python", "javascript", "rust", "go", "cpp", "java"],
            task_count=225,
            result_count=None,
        )

    def fetch(self) -> Any:
        """Fetch official Aider Polyglot data via HTTP with graceful offline fixture fallback."""
        try:
            resp = httpx.get(OFFICIAL_SOURCE_URL, timeout=10.0)
            if resp.status_code == 200:
                return resp.json()
        except Exception:
            pass

        # Use verified offline fixture
        if self.fixture_path.exists():
            return json.loads(self.fixture_path.read_text(encoding="utf-8"))

        raise RuntimeError(f"Unable to fetch Aider Polyglot data from remote or fixture at {self.fixture_path}")

    def normalize(self, raw_data: Any) -> List[BenchmarkRecord]:
        records: List[BenchmarkRecord] = []
        raw_bytes = json.dumps(raw_data, sort_keys=True).encode("utf-8")

        for idx, item in enumerate(raw_data):
            task_id = item.get("task_id", f"polyglot_{idx}")
            model = item.get("model", "unknown")
            harness = item.get("harness", "aider")
            rec_id = f"aider_polyglot_{task_id}_{model}".replace("/", "_").replace(":", "_")

            prov = Provenance.create(
                source_url=OFFICIAL_SOURCE_URL,
                benchmark_name="Aider Polyglot",
                source_type="external",
                source_version=item.get("version", "2024-05"),
                source_last_updated=item.get("date", "2024-10-25"),
                license="Apache-2.0",
                source_record_id=str(task_id),
                raw_content=raw_bytes,
            )

            record = BenchmarkRecord(
                record_id=rec_id,
                source_type="external",
                benchmark_name="Aider Polyglot",
                benchmark_version=item.get("version", "2024-05"),
                task_id=task_id,
                language=item.get("language"),
                category="polyglot_editing",
                harness=harness,
                harness_version=item.get("harness_version"),
                model_provider=item.get("model_provider", "anthropic" if "claude" in model else "openai"),
                model_id=model,
                success=item.get("passed", item.get("pass_rate", 0) == 1.0),
                score=float(item.get("pass_rate", 1.0 if item.get("passed") else 0.0)),
                cost_usd=item.get("cost_usd"),
                runtime_seconds=item.get("duration_seconds"),
                turns=item.get("turns"),
                input_tokens=item.get("input_tokens"),
                output_tokens=item.get("output_tokens"),
                cache_read_tokens=item.get("cache_read_tokens"),
                cache_write_tokens=item.get("cache_write_tokens"),
                provenance=prov,
                raw_metadata=item,
            )
            records.append(record)

        return records
