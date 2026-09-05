"""SWE-bench benchmark dataset adapter (Verified & Lite)."""

import json
from pathlib import Path
from typing import Any, List, Optional
import httpx

from harnessbench.datasets.base import BenchmarkDatasetAdapter
from harnessbench.datasets.models import BenchmarkRecord, DatasetMetadata
from harnessbench.datasets.provenance import Provenance

OFFICIAL_SOURCE_URL = "https://raw.githubusercontent.com/princeton-nlp/SWE-bench/main/docs/leaderboard.json"
FIXTURE_PATH = Path(__file__).resolve().parent.parent.parent.parent.parent / "tests" / "fixtures" / "swebench" / "swebench_results.json"


class SWEBenchAdapter(BenchmarkDatasetAdapter):
    """Adapter for ingesting official SWE-bench evaluation results."""

    def __init__(self, fixture_override: Optional[Path] = None):
        self.fixture_path = fixture_override or FIXTURE_PATH

    def metadata(self) -> DatasetMetadata:
        return DatasetMetadata(
            name="swebench",
            display_name="SWE-bench (Verified & Lite)",
            description="Evaluates language models on real GitHub software engineering issues across popular Python repositories.",
            source_url=OFFICIAL_SOURCE_URL,
            license="MIT",
            version="v1.0",
            last_updated="2024-11-01",
            languages=["python"],
            task_count=500,
            result_count=None,
        )

    def fetch(self) -> Any:
        """Fetch official SWE-bench data via HTTP with graceful offline fixture fallback."""
        try:
            resp = httpx.get(OFFICIAL_SOURCE_URL, timeout=10.0)
            if resp.status_code == 200:
                return resp.json()
        except Exception:
            pass

        if self.fixture_path.exists():
            return json.loads(self.fixture_path.read_text(encoding="utf-8"))

        raise RuntimeError(f"Unable to fetch SWE-bench data from remote or fixture at {self.fixture_path}")

    def normalize(self, raw_data: Any) -> List[BenchmarkRecord]:
        records: List[BenchmarkRecord] = []
        raw_bytes = json.dumps(raw_data, sort_keys=True).encode("utf-8")

        for idx, item in enumerate(raw_data):
            inst_id = item.get("instance_id", f"swebench_inst_{idx}")
            model = item.get("model_name", item.get("model", "unknown"))
            agent = item.get("agent", item.get("harness", "unknown"))
            bench_name = item.get("benchmark", "SWE-bench")
            rec_id = f"swebench_{inst_id}_{model}_{agent}".replace("/", "_").replace(":", "_")

            metrics = item.get("metrics", {})

            prov = Provenance.create(
                source_url=OFFICIAL_SOURCE_URL,
                benchmark_name=bench_name,
                source_type="external",
                source_version=item.get("version", "v1.0"),
                source_last_updated=item.get("created_at", "2024-11-01"),
                license="MIT",
                source_record_id=str(inst_id),
                raw_content=raw_bytes,
            )

            resolved = item.get("resolved")
            score = 1.0 if resolved else 0.0 if resolved is not None else None

            record = BenchmarkRecord(
                record_id=rec_id,
                source_type="external",
                benchmark_name=bench_name,
                benchmark_version=item.get("version", "v1.0"),
                task_id=inst_id,
                language=item.get("language", "python"),
                category="github_issue_resolution",
                harness=agent,
                harness_version=item.get("agent_version"),
                model_provider="anthropic" if "claude" in model.lower() else "openai" if "gpt" in model.lower() else None,
                model_id=model,
                success=resolved,
                score=score,
                cost_usd=metrics.get("cost_usd"),
                runtime_seconds=metrics.get("duration_seconds"),
                turns=metrics.get("turns"),
                files_changed=metrics.get("files_changed"),
                lines_added=metrics.get("lines_added"),
                lines_removed=metrics.get("lines_removed"),
                provenance=prov,
                raw_metadata=item,
            )
            records.append(record)

        return records
