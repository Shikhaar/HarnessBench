"""Domain models for HarnessBench cross-language benchmarking framework."""

from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, Field


class BenchmarkTask(BaseModel):
    """Specification of a generic, cross-language benchmark task."""
    id: str = Field(..., description="Unique task identifier, e.g. typescript_api_001")
    name: str = Field(..., description="Human-readable task name")
    language: str = Field("python", description="Programming language: python, typescript, go, java, etc.")
    category: str = Field("bug_fixing", description="Software engineering category, e.g. concurrency, api, refactoring")
    difficulty: str = Field("medium", description="Task difficulty: easy, medium, hard")
    description: str = Field("", description="Task description and goals")
    repository: Optional[str] = Field(None, description="Path to seed repository template")
    prompt_path: Optional[Path] = Field(None, description="Path to task prompt markdown file")
    evaluation_command: Union[str, List[str]] = Field(..., description="Generic command to evaluate task completion")
    baseline_command: Union[str, List[str]] = Field(..., description="Generic command to verify baseline state")
    golden_patch_path: Optional[Path] = Field(None, description="Path to golden reference patch")
    expected_files: List[str] = Field(default_factory=list, description="Files legitimately expected to be modified")
    timeout_seconds: int = Field(300, description="Task execution timeout in seconds")


class HarnessConfig(BaseModel):
    """Configuration for launching an agent harness."""
    name: str = Field(..., description="Name of the harness, e.g., claude, aider, codeless")
    command: List[str] = Field(default_factory=list, description="Command tokens template")
    environment: Dict[str, str] = Field(default_factory=dict, description="Environment variables injected")
    timeout_seconds: int = Field(300, description="Maximum execution time allowed")


class HarnessExecutionResult(BaseModel):
    """Raw process result from running an agent harness."""
    exit_code: int
    stdout: str
    stderr: str
    duration: float


class PollutionReport(BaseModel):
    """Report detailing repository pollution and unexpected filesystem mutations."""
    unexpected_files: List[str] = Field(default_factory=list, description="Untracked files or unexpected new files")
    unexpected_directories: List[str] = Field(default_factory=list, description="Untracked newly created directories")
    unrelated_modifications: List[str] = Field(default_factory=list, description="Tracked files modified outside expected_files")
    pollution_score: int = Field(0, description="Calculated pollution penalty score")


class PatchQualityMetrics(BaseModel):
    """Metrics assessing the minimalism, cleanliness, and quality of agent changes."""
    files_changed: int = 0
    lines_added: int = 0
    lines_deleted: int = 0
    diff_size: int = 0
    unexpected_files: List[str] = Field(default_factory=list)
    unrelated_modifications: List[str] = Field(default_factory=list)
    quality_score: float = 1.0


class RunResult(BaseModel):
    """Comprehensive, reproducible outcome of a single task execution by a harness."""
    run_id: str
    task_id: str
    harness: str
    model: str
    language: str = "python"
    category: str = "bug_fixing"
    repetition_index: int = 1

    success: bool

    input_tokens: int = 0
    output_tokens: int = 0
    cache_read_tokens: int = 0
    total_tokens: int = 0

    cost_usd: float = 0.0
    cost_per_successful_task: Optional[float] = None
    tokens_per_successful_task: Optional[int] = None

    turn_count: Optional[int] = None
    duration_seconds: float = 0.0
    time_to_first_api_request: Optional[float] = None

    files_changed: int = 0
    lines_added: int = 0
    lines_deleted: int = 0

    unexpected_files: List[str] = Field(default_factory=list)
    pollution_score: int = 0
    patch_quality: Optional[PatchQualityMetrics] = None

    pre_existing_tests_passed: bool = True
    post_tests_passed: bool = False
    regression_detected: bool = False

    timeout: bool = False
    budget_exceeded: bool = False
    status: str = "passed"
    harness_exit_code: int = 0
    evaluation_exit_code: int = 0
    api_errors: int = 0

    stdout: str = ""
    stderr: str = ""

    git_diff: str = ""
    git_status: str = ""

    started_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: datetime = Field(default_factory=datetime.utcnow)

    # Metadata for reproducibility
    harnessbench_version: str = "0.1.0"
    python_version: str = ""
    os_info: str = ""
    git_commit: Optional[str] = None
    extra_metadata: Dict[str, Any] = Field(default_factory=dict)


class TaskValidationResult(BaseModel):
    """Outcome of validating a task against baseline, golden patch, and evaluation."""
    task_id: str
    language: str
    valid: bool
    status: str = "VALID"
    environment_available: bool = True
    baseline_pre_passed: bool
    eval_pre_failed: bool
    golden_patch_applied: bool
    eval_post_passed: bool
    baseline_post_passed: bool
    errors: List[str] = Field(default_factory=list)


class BenchmarkManifest(BaseModel):
    """Manifest describing an immutable official benchmark run."""
    benchmark_version: str = "0.1.0"
    task_suite_version: str = "0.1.0"
    model: str
    provider: str
    repetitions: int = 1
    harnesses: Dict[str, str] = Field(default_factory=dict)
    environment: Dict[str, str] = Field(default_factory=dict)
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    git_commit: Optional[str] = None


class AggregateHarnessStats(BaseModel):
    """Statistical aggregation for a harness across repeated runs and tasks."""
    harness: str
    model: str
    total_runs: int = 0
    tasks_total: int = 0
    tasks_passed: int = 0
    pass_rate_mean: float = 0.0
    pass_rate_stddev: float = 0.0
    cost_total_usd: float = 0.0
    cost_mean_usd: float = 0.0
    cost_per_successful_task: float = 0.0
    tokens_mean: float = 0.0
    tokens_per_successful_task: float = 0.0
    latency_median: float = 0.0
    latency_mean: float = 0.0
    pollution_score_mean: float = 0.0
    regression_rate: float = 0.0
    category_breakdown: Dict[str, float] = Field(default_factory=dict)
    language_breakdown: Dict[str, float] = Field(default_factory=dict)


class BenchmarkReport(BaseModel):
    """Aggregate benchmark report containing all runs, manifest, and summary."""
    benchmark_id: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    model: str
    manifest: Optional[BenchmarkManifest] = None
    runs: List[RunResult] = Field(default_factory=list)
    summary: Dict[str, Any] = Field(default_factory=dict)
    awards: Dict[str, str] = Field(default_factory=dict)
