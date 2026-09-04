"""Domain models for HarnessBench."""

from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class BenchmarkTask(BaseModel):
    """Specification of a benchmark task."""
    id: str = Field(..., description="Unique task identifier, e.g. python_bugfix_001")
    name: str = Field(..., description="Human-readable task name")
    description: str = Field(..., description="Description of the bug, refactor, or issue")
    repository: Optional[str] = Field(None, description="Path or reference to base repository template")
    prompt_path: Path = Field(..., description="Path to prompt markdown file")
    evaluation_command: List[str] = Field(default_factory=lambda: ["pytest"], description="Command to evaluate task completion")
    baseline_command: List[str] = Field(default_factory=lambda: ["pytest"], description="Command to verify baseline state")
    golden_patch_path: Optional[Path] = Field(None, description="Path to golden reference patch")
    expected_files: List[str] = Field(default_factory=list, description="Files legitimately expected to be modified")


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


class RunResult(BaseModel):
    """Comprehensive, reproducible outcome of a single task execution by a harness."""
    run_id: str
    task_id: str
    harness: str
    model: str

    success: bool

    input_tokens: int = 0
    output_tokens: int = 0
    cache_read_tokens: int = 0
    total_tokens: int = 0

    cost_usd: float = 0.0

    turn_count: int = 0
    duration_seconds: float = 0.0

    files_changed: int = 0
    lines_added: int = 0
    lines_deleted: int = 0

    unexpected_files: List[str] = Field(default_factory=list)
    pollution_score: int = 0

    pre_existing_tests_passed: bool = True
    post_tests_passed: bool = False
    regression_detected: bool = False

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


class BenchmarkReport(BaseModel):
    """Aggregate benchmark report containing all runs."""
    benchmark_id: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    model: str
    runs: List[RunResult] = Field(default_factory=list)
    summary: Dict[str, Any] = Field(default_factory=dict)
