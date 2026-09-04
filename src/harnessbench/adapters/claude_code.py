"""Claude Code CLI agent adapter."""

from pathlib import Path
from typing import Dict, List, Optional
from harnessbench.adapters.base import BaseHarnessAdapter
from harnessbench.execution.process import run_command_safe
from harnessbench.models import HarnessExecutionResult


class ClaudeCodeAdapter(BaseHarnessAdapter):
    """Adapter for Anthropic's Claude Code CLI (claude -p "<prompt>")."""

    @property
    def name(self) -> str:
        return "claude_code"

    def setup(self, cwd: Path, env: Dict[str, str]) -> None:
        """Setup for Claude Code execution."""
        pass

    def run(
        self,
        prompt: str,
        cwd: Path,
        env: Dict[str, str],
        timeout: int = 300,
    ) -> HarnessExecutionResult:
        # Standard non-interactive headless command for Claude Code
        cmd = [
            "claude",
            "-p",
            prompt,
        ]
        return run_command_safe(cmd, cwd=cwd, env=env, timeout=timeout)

    def teardown(self, cwd: Path) -> None:
        """Teardown any Claude Code temporary artifacts."""
        pass
