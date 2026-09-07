"""Registry and manager for external benchmark dataset adapters."""

from pathlib import Path
from typing import Dict, List, Optional, Tuple, Type

from harnessbench.datasets.adapters.aider_polyglot import AiderPolyglotAdapter
from harnessbench.datasets.adapters.openhands import OpenHandsAdapter
from harnessbench.datasets.adapters.swebench import SWEBenchAdapter
from harnessbench.datasets.base import BenchmarkDatasetAdapter
from harnessbench.datasets.models import BenchmarkRecord, DatasetMetadata

DEFAULT_RESULTS_DIR = Path(__file__).resolve().parent.parent.parent.parent / "results" / "external"

DATASET_ADAPTERS: Dict[str, Type[BenchmarkDatasetAdapter]] = {
    "aider-polyglot": AiderPolyglotAdapter,
    "swebench": SWEBenchAdapter,
    "openhands": OpenHandsAdapter,
}


def list_dataset_names() -> List[str]:
    """Return all registered external dataset names."""
    return sorted(list(DATASET_ADAPTERS.keys()))


def get_adapter(name: str) -> BenchmarkDatasetAdapter:
    """Retrieve an instantiated dataset adapter by name or raise ValueError."""
    normalized_name = name.strip().lower().replace("_", "-")
    adapter_cls = DATASET_ADAPTERS.get(normalized_name)
    if not adapter_cls:
        available = ", ".join(list_dataset_names())
        raise ValueError(f"Unknown benchmark dataset '{name}'. Available datasets: {available}")
    return adapter_cls()


def list_adapters() -> List[BenchmarkDatasetAdapter]:
    """Return instances of all registered dataset adapters."""
    return [cls() for cls in DATASET_ADAPTERS.values()]


def fetch_and_save_dataset(
    name: str,
    output_root: Optional[Path] = None,
) -> Tuple[DatasetMetadata, int, Path]:
    """Fetch official external dataset, normalize records, and persist to results/external/<name>/."""
    adapter = get_adapter(name)
    raw_data = adapter.fetch()
    records = adapter.normalize(raw_data)

    target_root = output_root or DEFAULT_RESULTS_DIR
    dataset_dir = target_root / adapter.metadata().name
    saved_path = adapter.save(records, dataset_dir)

    return adapter.metadata(), len(records), saved_path


def load_dataset_records(
    name: str,
    results_root: Optional[Path] = None,
) -> List[BenchmarkRecord]:
    """Load normalized records for a specific dataset from records.jsonl."""
    root = results_root or DEFAULT_RESULTS_DIR
    target = root / name / "records.jsonl"
    if not target.exists():
        # Attempt fallback to fixture if available
        adapter = get_adapter(name)
        raw_data = adapter.fetch()
        return adapter.normalize(raw_data)

    records: List[BenchmarkRecord] = []
    with target.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                records.append(BenchmarkRecord.model_validate_json(line))
    return records


def load_all_external_records(
    results_root: Optional[Path] = None,
) -> List[BenchmarkRecord]:
    """Load all ingested external reference benchmark records across all datasets."""
    all_records: List[BenchmarkRecord] = []
    for name in list_dataset_names():
        try:
            recs = load_dataset_records(name, results_root)
            all_records.extend(recs)
        except Exception:
            continue
    return all_records
