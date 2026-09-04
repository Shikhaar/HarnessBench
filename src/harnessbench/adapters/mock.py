"""Mock harness adapter for testing, validation, and dry-runs."""

import os
from pathlib import Path
from typing import Dict, List, Optional
from harnessbench.adapters.base import BaseHarnessAdapter
from harnessbench.models import HarnessExecutionResult


class MockAdapter(BaseHarnessAdapter):
    """Configurable mock harness adapter for testing HarnessBench without external dependencies."""

    def __init__(
        self,
        behavior: str = "solve",
        pollute: bool = False,
        fail: bool = False,
        timeout: bool = False,
        extra_stdout: str = "Mock agent executed successfully.",
    ):
        self.behavior = behavior
        self.pollute = pollute
        self.fail = fail
        self.timeout = timeout
        self.extra_stdout = extra_stdout

    @property
    def name(self) -> str:
        return "mock"

    def setup(self, cwd: Path, env: Dict[str, str]) -> None:
        pass

    def run(
        self,
        prompt: str,
        cwd: Path,
        env: Dict[str, str],
        timeout: int = 300,
    ) -> HarnessExecutionResult:
        if self.timeout:
            return HarnessExecutionResult(
                exit_code=-1,
                stdout="",
                stderr="[HarnessBench] Process timed out.",
                duration=float(timeout),
            )

        if self.fail:
            return HarnessExecutionResult(
                exit_code=1,
                stdout="Attempting to fix...",
                stderr="Error: failed to locate relevant code.",
                duration=0.5,
            )

        # Simulate repo pollution if requested
        if self.pollute:
            scratch_file = cwd / "agent_notes_scratch.md"
            scratch_file.write_text("# Scratchpad\nAnalysis of problem...", encoding="utf-8")

        # If behavior is solve and golden patch or fix script exists in task
        # Check if golden_patch is present or apply fix logic
        # Or look for a .golden_solution.patch in parent
        golden_patch = cwd / ".task_golden.patch"
        if golden_patch.exists():
            import subprocess
            subprocess.run(
                ["git", "apply", "--ignore-whitespace", "--whitespace=nowarn", str(golden_patch)],
                cwd=str(cwd),
                capture_output=True,
            )

        return HarnessExecutionResult(
            exit_code=0,
            stdout=self.extra_stdout,
            stderr="",
            duration=1.2,
        )

    def teardown(self, cwd: Path) -> None:
        pass
