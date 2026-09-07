"""Evaluation engine coordinating generic test suites, regressions, repo pollution, and patch quality."""

from harnessbench.evaluation.patch_quality import evaluate_patch_quality
from harnessbench.evaluation.pollution import analyze_repository_pollution
from harnessbench.evaluation.regression import check_regression
from harnessbench.evaluation.tests import execute_test_command
from harnessbench.execution.sandbox import SandboxWorkspace
from harnessbench.models import BenchmarkTask, PatchQualityMetrics, PollutionReport


class EvaluationOutcome:
    """Outcome of evaluating a completed harness execution."""

    def __init__(
        self,
        success: bool,
        pre_existing_tests_passed: bool,
        post_tests_passed: bool,
        regression_detected: bool,
        pollution_report: PollutionReport,
        patch_quality: PatchQualityMetrics,
        evaluation_exit_code: int,
        stdout: str = "",
        stderr: str = "",
    ):
        self.success = success
        self.pre_existing_tests_passed = pre_existing_tests_passed
        self.post_tests_passed = post_tests_passed
        self.regression_detected = regression_detected
        self.pollution_report = pollution_report
        self.patch_quality = patch_quality
        self.evaluation_exit_code = evaluation_exit_code
        self.stdout = stdout
        self.stderr = stderr


def evaluate_task_run(
    task: BenchmarkTask,
    sandbox: SandboxWorkspace,
    baseline_passed: bool,
    baseline_exit_code: int,
) -> EvaluationOutcome:
    """Execute evaluation tests, assess regressions, inspect repo pollution and patch quality."""
    # 1. Run generic evaluation test command (e.g. npm test, pytest, go test, mvn test)
    post_passed, post_code, stdout, stderr, _ = execute_test_command(
        command=task.evaluation_command,
        cwd=sandbox.path,
        timeout=task.timeout_seconds,
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

    # 4. Assess patch quality
    files_changed, lines_added, lines_deleted = sandbox.get_diff_stat()
    diff_text = sandbox.get_diff()
    patch_quality = evaluate_patch_quality(
        files_changed=files_changed,
        lines_added=lines_added,
        lines_deleted=lines_deleted,
        diff_text=diff_text,
        pollution=pollution,
    )

    # 5. Overall success: evaluation test passed AND baseline didn't regress
    overall_success = post_passed and (not regression.regression_detected)

    return EvaluationOutcome(
        success=overall_success,
        pre_existing_tests_passed=baseline_passed,
        post_tests_passed=post_passed,
        regression_detected=regression.regression_detected,
        pollution_report=pollution,
        patch_quality=patch_quality,
        evaluation_exit_code=post_code,
        stdout=stdout,
        stderr=stderr,
    )
