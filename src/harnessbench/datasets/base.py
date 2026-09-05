"""Abstract base adapter for importing, validating, and normalizing external benchmark datasets."""

from abc import ABC, abstractmethod
import json
from pathlib import Path
from typing import Any, List
from harnessbench.datasets.models import BenchmarkRecord, DatasetMetadata


class BenchmarkDatasetAdapter(ABC):
    """Abstract base class for benchmark dataset ingestion adapters."""

    @abstractmethod
    def metadata(self) -> DatasetMetadata:
        """Return dataset metadata describing source, languages, version, and license."""
        pass

    @abstractmethod
    def fetch(self) -> Any:
        """Fetch raw benchmark data from the official public source."""
        pass

    @abstractmethod
    def normalize(self, raw_data: Any) -> List[BenchmarkRecord]:
        """Convert raw benchmark data into normalized BenchmarkRecord instances."""
        pass

    def save(self, records: List[BenchmarkRecord], output_dir: Path) -> Path:
        """Persist normalized dataset to results/external/<name>/ with manifest and metadata."""
        output_dir.mkdir(parents=True, exist_ok=True)
        meta = self.metadata()

        # 1. metadata.json
        meta_path = output_dir / "metadata.json"
        meta_dict = meta.model_dump(mode="json")
        meta_dict["result_count"] = len(records)
        meta_path.write_text(json.dumps(meta_dict, indent=2), encoding="utf-8")

        # 2. records.jsonl
        records_path = output_dir / "records.jsonl"
        with records_path.open("w", encoding="utf-8") as f:
            for rec in records:
                f.write(rec.model_dump_json() + "\n")

        # 3. manifest.json
        manifest_path = output_dir / "manifest.json"
        first_prov = records[0].provenance if records else None
        manifest = {
            "dataset_name": meta.name,
            "source_url": meta.source_url,
            "license": meta.license,
            "version": meta.version,
            "last_updated": meta.last_updated,
            "retrieved_at": first_prov.retrieved_at.isoformat() if first_prov else None,
            "retrieval_hash": first_prov.retrieval_hash if first_prov else None,
            "record_count": len(records),
            "adapter": self.__class__.__name__,
        }
        manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")

        return output_dir
