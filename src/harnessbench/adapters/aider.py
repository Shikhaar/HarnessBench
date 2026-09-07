"""Aider coding agent adapter."""

from pathlib import Path
from typing import Dict
from harnessbench.adapters.base import BaseHarnessAdapter
from harnessbench.execution.process import run_command_safe
from harnessbench.models import HarnessExecutionResult


class AiderAdapter(BaseHarnessAdapter):
    """Adapter for Aider (https://github.com/paul-gauthier/aider)."""

    @property
    def name(self) -> str:
        return "aider"

    def setup(self, cwd: Path, env: Dict[str, str]) -> None:
        """Aider requires no special setup prior to execution."""
        pass

    def run(
        self,
        prompt: str,
        cwd: Path,
        env: Dict[str, str],
        timeout: int = 300,
    ) -> HarnessExecutionResult:
        # Standard non-interactive autonomous command for Aider
        cmd = [
            "aider",
            "--message",
            prompt,
            "--yes",
            "--no-git",
        ]
        return run_command_safe(cmd, cwd=cwd, env=env, timeout=timeout)

    def teardown(self, cwd: Path) -> None:
        """Teardown any temporary aider caches or config files if needed."""
        pass
