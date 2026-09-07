"""Base adapter interface for agent harnesses."""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict
from harnessbench.models import HarnessExecutionResult


class BaseHarnessAdapter(ABC):
    """Abstract base class defining the lifecycle of an AI coding agent harness."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Unique identifier for this harness."""
        pass

    @abstractmethod
    def setup(self, cwd: Path, env: Dict[str, str]) -> None:
        """Perform any pre-execution workspace preparation or config generation."""
        pass

    @abstractmethod
    def run(
        self,
        prompt: str,
        cwd: Path,
        env: Dict[str, str],
        timeout: int = 300,
    ) -> HarnessExecutionResult:
        """Execute the harness on a prompt within an isolated workspace directory."""
        pass

    @abstractmethod
    def teardown(self, cwd: Path) -> None:
        """Perform any post-execution cleanup specific to this harness."""
        pass
