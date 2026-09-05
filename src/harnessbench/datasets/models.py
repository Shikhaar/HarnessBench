"""Normalized domain models for external and controlled benchmark records."""

from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel, Field
from harnessbench.datasets.provenance import Provenance


class DatasetMetadata(BaseModel):
    """Metadata describing a benchmark dataset source."""

    name: str = Field(..., description="Unique slug for the dataset (e.g. aider-polyglot, swebench)")
    display_name: str = Field(..., description="Human-readable title")
    description: str = Field(..., description="Short summary of the benchmark")
    source_url: str = Field(..., description="Official homepage or repository")
    license: str = Field(..., description="Dataset license identifier")
    version: Optional[str] = Field(None, description="Current version, release, or tag")
    last_updated: Optional[str] = Field(None, description="Date when source was last updated")
    languages: List[str] = Field(default_factory=list, description="Supported programming languages")
    task_count: Optional[int] = Field(None, description="Total tasks in benchmark suite")
    result_count: Optional[int] = Field(None, description="Total benchmark evaluation records available")


class BenchmarkRecord(BaseModel):
    """Normalized cross-benchmark evaluation record.

    Represents an atomic execution result from either a controlled HarnessBench run
    or an ingested external reference benchmark (Aider Polyglot, SWE-bench, OpenHands).
    Missing values remain None and are never fabricated.
    """

    record_id: str = Field(..., description="Unique record identifier")
    source_type: Literal["harnessbench", "external"] = Field(
        ..., description="Origin classification: controlled harnessbench or external reference"
    )
    benchmark_name: str = Field(..., description="Name of the benchmark suite")
    benchmark_version: Optional[str] = Field(None, description="Benchmark version/variant")
    task_id: Optional[str] = Field(None, description="Task or problem instance identifier")
    language: Optional[str] = Field(None, description="Programming language of the task")
    category: Optional[str] = Field(None, description="Software engineering task category")

    harness: Optional[str] = Field(None, description="Agent harness or runtime name")
    harness_version: Optional[str] = Field(None, description="Version of the harness")

    model_provider: Optional[str] = Field(None, description="LLM provider name (e.g. anthropic, openai)")
    model_id: Optional[str] = Field(None, description="Exact model identifier")

    success: Optional[bool] = Field(None, description="Whether the task was solved successfully")
    score: Optional[float] = Field(None, description="Resolved percentage or quantitative score")

    cost_usd: Optional[float] = Field(None, description="Financial API cost in USD")
    runtime_seconds: Optional[float] = Field(None, description="Total wall-clock runtime in seconds")
    turns: Optional[int] = Field(None, description="Interaction turns taken by the agent")

    input_tokens: Optional[int] = Field(None, description="Total prompt / input tokens")
    output_tokens: Optional[int] = Field(None, description="Total completion / output tokens")
    cache_read_tokens: Optional[int] = Field(None, description="Cache read input tokens")
    cache_write_tokens: Optional[int] = Field(None, description="Cache creation / write tokens")

    files_changed: Optional[int] = Field(None, description="Number of files touched")
    lines_added: Optional[int] = Field(None, description="Lines of code added")
    lines_removed: Optional[int] = Field(None, description="Lines of code deleted")

    regression: Optional[bool] = Field(None, description="Whether pre-existing passing tests were broken")
    pollution: Optional[float] = Field(None, description="Repository pollution score")

    provenance: Provenance = Field(..., description="Full source provenance and retrieval metadata")
    raw_metadata: Dict[str, Any] = Field(
        default_factory=dict, description="Preserved unparsed raw attributes from the source"
    )
