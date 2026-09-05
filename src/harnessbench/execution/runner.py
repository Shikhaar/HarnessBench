"""Benchmark runner orchestrating cross-language sandboxes, adapters, proxies, and evaluation."""

import json
import os
import platform
import subprocess
import sys
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import httpx

from harnessbench import __version__
from harnessbench.adapters.base import BaseHarnessAdapter
from harnessbench.evaluation.evaluator import evaluate_task_run
from harnessbench.evaluation.tests import execute_test_command
from harnessbench.execution.sandbox import SandboxWorkspace
from harnessbench.models import BenchmarkTask, RunResult
from harnessbench.telemetry.costs import calculate_api_cost
from harnessbench.telemetry.events import EventRecorder, TelemetryEventType


def get_current_git_commit() -> Optional[str]:
    """Retrieve git HEAD commit of HarnessBench codebase if available."""
    try:
        res = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            timeout=2,
        )
        if res.returncode == 0:
            return res.stdout.strip()
    except Exception:
        pass
    return None


class BenchmarkRunner:
    """Executes a benchmark run for a specific task and harness combination."""

    def __init__(
        self,
        task: BenchmarkTask,
        adapter: BaseHarnessAdapter,
        model: str = "claude-3-5-sonnet-20241022",
        repetition_index: int = 1,
        proxy_url: Optional[str] = None,
        timeout: Optional[int] = None,
        output_dir: Optional[Path] = None,
    ):
        self.task = task
        self.adapter = adapter
        self.model = model
        self.repetition_index = repetition_index
        self.proxy_url = proxy_url
        self.timeout = timeout or task.timeout_seconds
        self.output_dir = output_dir or Path("results")
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def run(self) -> RunResult:
        run_id = f"{self.adapter.name}_{self.task.id}_rep{self.repetition_index}_{uuid.uuid4().hex[:6]}"
        events = EventRecorder(run_id=run_id)
        started_at = datetime.utcnow()
        events.record(
            TelemetryEventType.RUN_STARTED,
            task_id=self.task.id,
            harness=self.adapter.name,
            model=self.model,
            repetition=self.repetition_index,
        )

        template_dir = Path(self.task.repository) if self.task.repository else None
        sandbox = SandboxWorkspace(
            task_id=self.task.id,
            template_dir=template_dir,
            golden_patch_path=self.task.golden_patch_path,
        )

        with sandbox:
            # 1. Baseline tests in clean repository
            events.record(TelemetryEventType.TESTS_STARTED, phase="baseline")
            baseline_passed, baseline_code, b_stdout, b_stderr, _ = execute_test_command(
                command=self.task.baseline_command,
                cwd=sandbox.path,
                timeout=self.timeout,
            )
            events.record(TelemetryEventType.TESTS_FINISHED, phase="baseline", passed=baseline_passed)

            # 2. Configure proxy session if proxy is active
            if self.proxy_url:
                try:
                    httpx.post(
                        f"{self.proxy_url}/proxy/session/start",
                        json={
                            "run_id": run_id,
                            "task_id": self.task.id,
                            "harness": self.adapter.name,
                            "model": self.model,
                        },
                        timeout=5.0,
                    )
                except Exception:
                    pass

            # 3. Prepare environment
            env: Dict[str, str] = {
                "HARNESSBENCH_RUN_ID": run_id,
                "HARNESSBENCH_TASK_ID": self.task.id,
                "HARNESSBENCH_MODEL": self.model,
                "HARNESSBENCH_LANGUAGE": self.task.language,
            }
            if self.proxy_url:
                env["ANTHROPIC_BASE_URL"] = self.proxy_url
                env["OPENAI_BASE_URL"] = self.proxy_url

            # 4. Read prompt
            prompt_content = ""
            if self.task.prompt_path and self.task.prompt_path.exists():
                prompt_content = self.task.prompt_path.read_text(encoding="utf-8")
            else:
                prompt_content = f"Solve the issue in task {self.task.id}: {self.task.description}"

            # 5. Launch harness
            events.record(TelemetryEventType.HARNESS_STARTED, harness=self.adapter.name)
            self.adapter.setup(cwd=sandbox.path, env=env)
            harness_exec = self.adapter.run(
                prompt=prompt_content,
                cwd=sandbox.path,
                env=env,
                timeout=self.timeout,
            )
            self.adapter.teardown(cwd=sandbox.path)
            events.record(
                TelemetryEventType.HARNESS_FINISHED,
                exit_code=harness_exec.exit_code,
                duration=harness_exec.duration,
            )

            # 6. Retrieve proxy telemetry
            input_tokens = 0
            output_tokens = 0
            cache_read_tokens = 0
            total_tokens = 0
            cost_usd = 0.0
            turn_count: Optional[int] = None
            time_to_first_req: Optional[float] = None
            api_errors = 0

            if self.proxy_url:
                try:
                    stop_resp = httpx.post(f"{self.proxy_url}/proxy/session/stop", timeout=5.0)
                    if stop_resp.status_code == 200:
                        pdata = stop_resp.json()
                        input_tokens = pdata.get("input_tokens", 0)
                        output_tokens = pdata.get("output_tokens", 0)
                        cache_read_tokens = pdata.get("cache_read_tokens", 0)
                        total_tokens = pdata.get("total_tokens", 0)
                        cost_usd = pdata.get("cost_usd", 0.0)
                        raw_turns = pdata.get("total_requests", 0)
                        turn_count = raw_turns if raw_turns > 0 else None
                        time_to_first_req = pdata.get("time_to_first_request")
                        api_errors = pdata.get("api_errors", 0)
                except Exception:
                    pass

            if cost_usd == 0.0 and (input_tokens > 0 or output_tokens > 0):
                cost_usd = calculate_api_cost(
                    model=self.model,
                    input_tokens=input_tokens,
                    output_tokens=output_tokens,
                    cache_read_tokens=cache_read_tokens,
                )

            # 7. Evaluate task completion, regressions, repo pollution, patch quality
            events.record(TelemetryEventType.TESTS_STARTED, phase="post_evaluation")
            eval_outcome = evaluate_task_run(
                task=self.task,
                sandbox=sandbox,
                baseline_passed=baseline_passed,
                baseline_exit_code=baseline_code,
            )
            events.record(
                TelemetryEventType.TESTS_FINISHED,
                phase="post_evaluation",
                passed=eval_outcome.post_tests_passed,
            )

            # 8. Git statistics
            files_changed, lines_added, lines_deleted = sandbox.get_diff_stat()
            git_diff = sandbox.get_diff()
            git_status = sandbox.get_status_porcelain()

            completed_at = datetime.utcnow()
            events.record(TelemetryEventType.RUN_FINISHED, success=eval_outcome.success)

            is_timeout = (harness_exec.exit_code == -1 or "timed out" in harness_exec.stderr.lower())
            if baseline_code == 127 or "Command not found" in (b_stderr or ""):
                status = "environment_unavailable"
                overall_success = False
            elif is_timeout:
                status = "timeout"
                overall_success = False
            elif harness_exec.exit_code != 0:
                status = "harness_failed"
                overall_success = False
            elif eval_outcome.success:
                status = "passed"
                overall_success = True
            else:
                status = "failed"
                overall_success = False

            result = RunResult(
                run_id=run_id,
                task_id=self.task.id,
                harness=self.adapter.name,
                model=self.model,
                language=self.task.language,
                category=self.task.category,
                repetition_index=self.repetition_index,
                success=overall_success,
                status=status,
                budget_exceeded=False,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                cache_read_tokens=cache_read_tokens,
                total_tokens=total_tokens,
                cost_usd=cost_usd,
                turn_count=turn_count,
                duration_seconds=harness_exec.duration,
                time_to_first_api_request=time_to_first_req,
                files_changed=files_changed,
                lines_added=lines_added,
                lines_deleted=lines_deleted,
                unexpected_files=eval_outcome.pollution_report.unexpected_files,
                pollution_score=eval_outcome.pollution_report.pollution_score,
                patch_quality=eval_outcome.patch_quality,
                pre_existing_tests_passed=eval_outcome.pre_existing_tests_passed,
                post_tests_passed=eval_outcome.post_tests_passed,
                regression_detected=eval_outcome.regression_detected,
                timeout=is_timeout,
                harness_exit_code=harness_exec.exit_code,
                evaluation_exit_code=eval_outcome.evaluation_exit_code,
                api_errors=api_errors,
                stdout=harness_exec.stdout,
                stderr=harness_exec.stderr,
                git_diff=git_diff,
                git_status=git_status,
                started_at=started_at,
                completed_at=completed_at,
                harnessbench_version=__version__,
                python_version=sys.version.split()[0],
                os_info=platform.platform(),
                git_commit=get_current_git_commit(),
                extra_metadata={"events": [e.model_dump() for e in events.get_events()]},
            )

            # Persist individual run result
            run_file = self.output_dir / f"{run_id}.json"
            run_file.write_text(result.model_dump_json(indent=2), encoding="utf-8")

            return result


def create_skipped_result(
    task: BenchmarkTask,
    harness_name: str,
    model: str,
    repetition_index: int = 1,
    reason: str = "skipped_budget_exceeded",
    output_dir: Optional[Path] = None,
) -> RunResult:
    """Create and persist a RunResult for tasks skipped due to budget or runtime limits."""
    run_id = f"{harness_name}_{task.id}_rep{repetition_index}_skipped_{uuid.uuid4().hex[:6]}"
    result = RunResult(
        run_id=run_id,
        task_id=task.id,
        harness=harness_name,
        model=model,
        language=task.language,
        category=task.category,
        repetition_index=repetition_index,
        success=False,
        status=reason,
        budget_exceeded=True,
        stdout=f"Task execution skipped: {reason}",
    )
    if output_dir:
        output_dir.mkdir(parents=True, exist_ok=True)
        (output_dir / f"{run_id}.json").write_text(result.model_dump_json(indent=2), encoding="utf-8")
    return result

