"""Generic language-agnostic test execution runner."""

import shlex
import sys
from pathlib import Path
from typing import List, Tuple, Union
from harnessbench.execution.process import run_command_safe


def normalize_command(command: Union[str, List[str]]) -> List[str]:
    """Convert a string or list command into an executable argument list."""
    if isinstance(command, list):
        cmd_list = list(command)
    else:
        cmd_str = command.strip()
        # Use shlex on posix, handle windows escaping appropriately
        try:
            cmd_list = shlex.split(cmd_str, posix=(sys.platform != "win32"))
        except Exception:
            cmd_list = cmd_str.split()

    if not cmd_list:
        return []

    # If invoking pytest, alias to the active virtual environment's python interpreter
    if cmd_list[0] == "pytest":
        cmd_list = [sys.executable, "-m", "pytest", "-o", "pythonpath=."] + cmd_list[1:]
    elif cmd_list[0] == "python" and sys.executable:
        cmd_list = [sys.executable] + cmd_list[1:]

    return cmd_list


def execute_test_command(
    command: Union[str, List[str]],
    cwd: Path,
    timeout: int = 120,
) -> Tuple[bool, int, str, str, float]:
    """Execute any generic language test command (npm test, pytest, go test, mvn test) in workspace.

    Returns:
        (passed, exit_code, stdout, stderr, duration)
    """
    cmd_list = normalize_command(command)
    if not cmd_list:
        return False, 1, "", "Empty evaluation command provided", 0.0

    result = run_command_safe(cmd_list, cwd=cwd, timeout=timeout)
    passed = (result.exit_code == 0)
    return passed, result.exit_code, result.stdout, result.stderr, result.duration
