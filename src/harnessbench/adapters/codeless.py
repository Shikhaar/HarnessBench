"""Codeless autonomous agent adapter."""

from pathlib import Path
from typing import Dict
from harnessbench.adapters.base import BaseHarnessAdapter
from harnessbench.execution.process import run_command_safe
from harnessbench.models import HarnessExecutionResult


class CodelessAdapter(BaseHarnessAdapter):
    """Adapter for Codeless (codeless --permission-mode full_auto -p "<prompt>")."""

    @property
    def name(self) -> str:
        return "codeless"

    def setup(self, cwd: Path, env: Dict[str, str]) -> None:
        """Setup for Codeless execution."""
        pass

    def run(
        self,
        prompt: str,
        cwd: Path,
        env: Dict[str, str],
        timeout: int = 300,
    ) -> HarnessExecutionResult:
        # Standard non-interactive headless command for Codeless
        cmd = [
            "codeless",
            "--permission-mode",
            "full_auto",
            "-p",
            prompt,
        ]
        return run_command_safe(cmd, cwd=cwd, env=env, timeout=timeout)

    def teardown(self, cwd: Path) -> None:
        """Teardown any Codeless session artifacts."""
        pass
