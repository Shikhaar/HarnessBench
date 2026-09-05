"""OpenHands evaluation benchmark index adapter."""

import json
from pathlib import Path
from typing import Any, List, Optional
import httpx

from harnessbench.datasets.base import BenchmarkDatasetAdapter
from harnessbench.datasets.models import BenchmarkRecord, DatasetMetadata
from harnessbench.datasets.provenance import Provenance

OFFICIAL_SOURCE_URL = "https://raw.githubusercontent.com/All-Hands-AI/OpenHands/main/evaluation/results/index.json"
FIXTURE_PATH = Path(__file__).resolve().parent.parent.parent.parent.parent / "tests" / "fixtures" / "openhands" / "openhands_results.json"


class OpenHandsAdapter(BenchmarkDatasetAdapter):
    """Adapter for ingesting official OpenHands evaluation benchmark results."""

    def __init__(self, fixture_override: Optional[Path] = None):
        self.fixture_path = fixture_override or FIXTURE_PATH

    def metadata(self) -> DatasetMetadata:
        return DatasetMetadata(
            name="openhands",
            display_name="OpenHands Evaluation Index",
            description="OpenHands autonomous agent evaluation records across SWE-bench and coding benchmarks.",
            source_url=OFFICIAL_SOURCE_URL,
            license="MIT",
            version="v0.12.0",
            last_updated="2024-11-10",
            languages=["python"],
            task_count=300,
            result_count=None,
        )

    def fetch(self) -> Any:
        """Fetch official OpenHands evaluation index via HTTP with graceful offline fixture fallback."""
        try:
            resp = httpx.get(OFFICIAL_SOURCE_URL, timeout=10.0)
            if resp.status_code == 200:
                return resp.json()
        except Exception:
            pass

        if self.fixture_path.exists():
            return json.loads(self.fixture_path.read_text(encoding="utf-8"))

        raise RuntimeError(f"Unable to fetch OpenHands data from remote or fixture at {self.fixture_path}")

    def normalize(self, raw_data: Any) -> List[BenchmarkRecord]:
        records: List[BenchmarkRecord] = []
        raw_bytes = json.dumps(raw_data, sort_keys=True).encode("utf-8")

        for idx, item in enumerate(raw_data):
            task_id = item.get("task_id", f"openhands_task_{idx}")
            model = item.get("model", "unknown")
            agent = item.get("agent_class", "OpenHandsAgent")
            bench_name = item.get("benchmark", "OpenHands Evaluation Index")
            rec_id = f"openhands_{task_id}_{model}_{agent}".replace("/", "_").replace(":", "_")

            prov = Provenance.create(
                source_url=OFFICIAL_SOURCE_URL,
                benchmark_name=bench_name,
                source_type="external",
                source_version=item.get("benchmark_version", "v0.12.0"),
                source_last_updated=item.get("date", "2024-11-10"),
                license="MIT",
                source_record_id=str(task_id),
                raw_content=raw_bytes,
            )

            success = item.get("success")
            score = 1.0 if success else 0.0 if success is not None else None

            record = BenchmarkRecord(
                record_id=rec_id,
                source_type="external",
                benchmark_name=bench_name,
                benchmark_version=item.get("benchmark_version", "v0.12.0"),
                task_id=task_id,
                language=item.get("language", "python"),
                category="autonomous_agent_resolution",
                harness=agent,
                harness_version=item.get("agent_version"),
                model_provider="anthropic" if "claude" in model.lower() else "openai" if "gpt" in model.lower() else None,
                model_id=model,
                success=success,
                score=score,
                cost_usd=item.get("accumulated_cost"),
                runtime_seconds=item.get("total_duration"),
                turns=item.get("total_turns"),
                input_tokens=item.get("input_tokens"),
                output_tokens=item.get("output_tokens"),
                cache_read_tokens=item.get("cache_read_tokens"),
                provenance=prov,
                raw_metadata=item,
            )
            records.append(record)

        return records
