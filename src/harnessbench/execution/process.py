"""Safe synchronous and asynchronous subprocess execution with timeouts, environment control, and secret scrubbing.

Follows Object-Oriented Software Principles (SRP, OCP, LSP, ISP, DIP).
"""

from abc import ABC, abstractmethod
import asyncio
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


class SecretScrubber:
    """Encapsulates redaction of secrets, tokens, and sensitive environment variables."""

    @staticmethod
    def scrub(text: str, env: Optional[Dict[str, str]] = None) -> str:
        """Scrub sensitive credentials and known secret tokens from text."""
        if not text:
            return ""
        scrubbed = text

        # Scrub values from environment if marked sensitive
        if env:
            for k, v in env.items():
                if v and len(v) >= 6 and any(s in k.upper() for s in SENSITIVE_ENV_KEYS):
                    scrubbed = scrubbed.replace(v, f"[REDACTED_{k}]")

        # Scrub standard sk-... and ant-... patterns
        scrubbed = re.sub(r"sk-[A-Za-z0-9_-]{20,}", "[REDACTED_API_KEY]", scrubbed)
        scrubbed = re.sub(r"ant-[A-Za-z0-9_-]{20,}", "[REDACTED_API_KEY]", scrubbed)
        return scrubbed


def scrub_secrets(text: str, env: Optional[Dict[str, str]] = None) -> str:
    """Convenience function delegating to SecretScrubber."""
    return SecretScrubber.scrub(text, env)


class IProcessRunner(ABC):
    """Abstract interface for process execution."""

    @abstractmethod
    def run(
        self,
        cmd: List[str],
        cwd: Path,
        env: Optional[Dict[str, str]] = None,
        timeout: int = 300,
    ) -> HarnessExecutionResult:
        """Execute a process synchronously."""
        pass

    @abstractmethod
    async def run_async(
        self,
        cmd: List[str],
        cwd: Path,
        env: Optional[Dict[str, str]] = None,
        timeout: int = 300,
    ) -> HarnessExecutionResult:
        """Execute a process asynchronously."""
        pass


class ProcessRunner(IProcessRunner):
    """Standard synchronous and asynchronous process runner."""

    def __init__(self, scrubber: Optional[SecretScrubber] = None) -> None:
        self.scrubber = scrubber or SecretScrubber()

    def run(
        self,
        cmd: List[str],
        cwd: Path,
        env: Optional[Dict[str, str]] = None,
        timeout: int = 300,
    ) -> HarnessExecutionResult:
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
            stdout=self.scrubber.scrub(stdout, merged_env),
            stderr=self.scrubber.scrub(stderr, merged_env),
            duration=duration,
        )

    async def run_async(
        self,
        cmd: List[str],
        cwd: Path,
        env: Optional[Dict[str, str]] = None,
        timeout: int = 300,
    ) -> HarnessExecutionResult:
        merged_env = os.environ.copy()
        if env:
            merged_env.update(env)

        start_time = time.perf_counter()
        try:
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                cwd=str(cwd),
                env=merged_env,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            try:
                stdout_bytes, stderr_bytes = await asyncio.wait_for(
                    proc.communicate(), timeout=float(timeout)
                )
                stdout = stdout_bytes.decode("utf-8", errors="replace")
                stderr = stderr_bytes.decode("utf-8", errors="replace")
                exit_code = proc.returncode or 0
            except asyncio.TimeoutError:
                try:
                    proc.kill()
                except ProcessLookupError:
                    pass
                stdout_bytes, stderr_bytes = await proc.communicate()
                stdout = stdout_bytes.decode("utf-8", errors="replace")
                stderr = stderr_bytes.decode("utf-8", errors="replace") + f"\n[HarnessBench] Process timed out after {timeout}s."
                exit_code = -1

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
            stdout=self.scrubber.scrub(stdout, merged_env),
            stderr=self.scrubber.scrub(stderr, merged_env),
            duration=duration,
        )


_default_runner = ProcessRunner()


def run_command_safe(
    cmd: List[str],
    cwd: Path,
    env: Optional[Dict[str, str]] = None,
    timeout: int = 300,
) -> HarnessExecutionResult:
    """Run command synchronously using default ProcessRunner."""
    return _default_runner.run(cmd=cmd, cwd=cwd, env=env, timeout=timeout)


async def run_command_safe_async(
    cmd: List[str],
    cwd: Path,
    env: Optional[Dict[str, str]] = None,
    timeout: int = 300,
) -> HarnessExecutionResult:
    """Run command asynchronously using default ProcessRunner."""
    return await _default_runner.run_async(cmd=cmd, cwd=cwd, env=env, timeout=timeout)
