"""Provenance models for tracking source integrity, retrieval hashes, and metadata."""

from datetime import datetime
import hashlib
from typing import Literal, Optional
from pydantic import BaseModel, Field


class Provenance(BaseModel):
    """Cryptographic and contextual provenance for benchmark records and dataset imports."""

    source_url: str = Field(..., description="Official URL where the raw data was fetched")
    retrieved_at: datetime = Field(default_factory=datetime.utcnow, description="UTC timestamp of retrieval")
    source_version: Optional[str] = Field(None, description="Official version, tag, or release of the source")
    source_last_updated: Optional[str] = Field(None, description="Date/timestamp when source was last updated")
    license: Optional[str] = Field(None, description="License of the source benchmark dataset")
    source_type: Literal["harnessbench", "external"] = Field(
        ..., description="Origin classification: controlled harnessbench or external reference"
    )
    benchmark_name: str = Field(..., description="Name of the benchmark suite (e.g. Aider Polyglot, SWE-bench)")
    source_record_id: Optional[str] = Field(None, description="Identifier of the record in the source system")
    retrieval_hash: Optional[str] = Field(None, description="SHA-256 hash of the retrieved raw artifact")

    @classmethod
    def create(
        cls,
        source_url: str,
        benchmark_name: str,
        source_type: Literal["harnessbench", "external"] = "external",
        source_version: Optional[str] = None,
        source_last_updated: Optional[str] = None,
        license: Optional[str] = None,
        source_record_id: Optional[str] = None,
        raw_content: Optional[bytes] = None,
    ) -> "Provenance":
        """Factory method computing SHA-256 hash of raw content if provided."""
        retrieval_hash = None
        if raw_content is not None:
            retrieval_hash = hashlib.sha256(raw_content).hexdigest()

        return cls(
            source_url=source_url,
            retrieved_at=datetime.utcnow(),
            source_version=source_version,
            source_last_updated=source_last_updated,
            license=license,
            source_type=source_type,
            benchmark_name=benchmark_name,
            source_record_id=source_record_id,
            retrieval_hash=retrieval_hash,
        )
