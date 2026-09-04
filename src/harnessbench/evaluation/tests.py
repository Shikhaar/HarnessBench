"""Automated test execution runner for baseline and post-evaluation suites."""

import sys
from pathlib import Path
from typing import List, Optional, Tuple
from harnessbench.execution.process import run_command_safe


def execute_test_command(
    command: List[str],
    cwd: Path,
    timeout: int = 60,
) -> Tuple[bool, int, str, str, float]:
    """Execute a test command (e.g. pytest) inside the sandbox workspace.

    Returns:
        (passed, exit_code, stdout, stderr, duration)
    """
    # Replace bare 'pytest' with [sys.executable, "-m", "pytest"] if appropriate
    final_cmd = list(command)
    if final_cmd and final_cmd[0] == "pytest":
        final_cmd = [sys.executable, "-m", "pytest", "-o", "pythonpath=."] + final_cmd[1:]

    result = run_command_safe(final_cmd, cwd=cwd, timeout=timeout)
    passed = (result.exit_code == 0)
    return passed, result.exit_code, result.stdout, result.stderr, result.duration
