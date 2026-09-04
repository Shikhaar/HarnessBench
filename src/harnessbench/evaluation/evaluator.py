"""Evaluation engine orchestrating test suites, regressions, and repo pollution."""

from pathlib import Path
from typing import Dict, List, Optional
from harnessbench.evaluation.pollution import analyze_repository_pollution
from harnessbench.evaluation.regression import check_regression
from harnessbench.evaluation.tests import execute_test_command
from harnessbench.execution.sandbox import SandboxWorkspace
from harnessbench.models import BenchmarkTask, PollutionReport


class EvaluationOutcome:
    """Outcome of evaluating a completed harness execution."""

    def __init__(
        self,
        success: bool,
        pre_existing_tests_passed: bool,
        post_tests_passed: bool,
        regression_detected: bool,
        pollution_report: PollutionReport,
        stdout: str = "",
        stderr: str = "",
    ):
        self.success = success
        self.pre_existing_tests_passed = pre_existing_tests_passed
        self.post_tests_passed = post_tests_passed
        self.regression_detected = regression_detected
        self.pollution_report = pollution_report
        self.stdout = stdout
        self.stderr = stderr


def evaluate_task_run(
    task: BenchmarkTask,
    sandbox: SandboxWorkspace,
    baseline_passed: bool,
    baseline_exit_code: int,
) -> EvaluationOutcome:
    """Execute evaluation tests, assess regressions, and inspect repo pollution."""
    # 1. Run evaluation test command (e.g., pytest test_eval.py)
    post_passed, post_code, stdout, stderr, _ = execute_test_command(
        command=task.evaluation_command,
        cwd=sandbox.path,
    )

    # 2. Check for regression
    regression = check_regression(
        baseline_exit_code=baseline_exit_code,
        post_exit_code=post_code,
    )

    # 3. Analyze pollution
    untracked = sandbox.get_untracked_files()
    modified = sandbox.get_modified_files()
    pollution = analyze_repository_pollution(
        untracked_files=untracked,
        modified_files=modified,
        expected_files=task.expected_files,
    )

    # 4. Determine overall success:
    # Full success requires evaluation tests to pass without inducing regressions
    overall_success = post_passed and (not regression.regression_detected)

    return EvaluationOutcome(
        success=overall_success,
        pre_existing_tests_passed=baseline_passed,
        post_tests_passed=post_passed,
        regression_detected=regression.regression_detected,
        pollution_report=pollution,
        stdout=stdout,
        stderr=stderr,
    )
