"""Safe subprocess execution with timeouts, environment control, and secret scrubbing."""

import os
import re
import subprocess
import time
from pathlib import Path
from typing import Dict, List, Optional
from harnessbench.models import HarnessExecutionResult

SENSITIVE_ENV_KEYS = [
    "ANTHROPIC_API_KEY",
    "OPENAI_API_KEY",
    "GITHUB_TOKEN",
    "AWS_SECRET_ACCESS_KEY",
    "API_KEY",
    "SECRET",
]


def scrub_secrets(text: str, env: Optional[Dict[str, str]] = None) -> str:
    """Scrub sensitive credentials and known secret tokens from text."""
    if not text:
        return ""
    scrubbed = text

    # Scrub values from environment if sensitive
    if env:
        for k, v in env.items():
            if v and len(v) >= 6 and any(s in k.upper() for s in SENSITIVE_ENV_KEYS):
                scrubbed = scrubbed.replace(v, f"[REDACTED_{k}]")

    # Scrub standard sk-... and ant-... patterns
    scrubbed = re.sub(r"sk-[A-Za-z0-9_-]{20,}", "[REDACTED_API_KEY]", scrubbed)
    scrubbed = re.sub(r"ant-[A-Za-z0-9_-]{20,}", "[REDACTED_API_KEY]", scrubbed)
    return scrubbed


def run_command_safe(
    cmd: List[str],
    cwd: Path,
    env: Optional[Dict[str, str]] = None,
    timeout: int = 300,
) -> HarnessExecutionResult:
    """Run a subprocess command safely with timeout and sanitized output."""
    merged_env = os.environ.copy()
    if env:
        merged_env.update(env)

    start_time = time.perf_counter()
    try:
        proc = subprocess.Popen(
            cmd,
            cwd=str(cwd),
            env=merged_env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            errors="replace",
            shell=False,
        )

        try:
            stdout, stderr = proc.communicate(timeout=timeout)
            exit_code = proc.returncode
        except subprocess.TimeoutExpired:
            proc.kill()
            stdout, stderr = proc.communicate()
            exit_code = -1
            stderr = f"{stderr}\n[HarnessBench] Process timed out after {timeout} seconds."

    except FileNotFoundError as e:
        return HarnessExecutionResult(
            exit_code=127,
            stdout="",
            stderr=f"Command not found: {cmd[0]} ({str(e)})",
            duration=0.0,
        )
    except Exception as e:
        return HarnessExecutionResult(
            exit_code=1,
            stdout="",
            stderr=f"Execution error: {str(e)}",
            duration=time.perf_counter() - start_time,
        )

    duration = time.perf_counter() - start_time

    return HarnessExecutionResult(
        exit_code=exit_code,
        stdout=scrub_secrets(stdout, merged_env),
        stderr=scrub_secrets(stderr, merged_env),
        duration=duration,
    )
