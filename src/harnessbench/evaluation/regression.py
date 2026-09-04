"""Regression analysis comparing baseline vs post-execution test outcomes."""

from pydantic import BaseModel


class RegressionResult(BaseModel):
    """Result of regression analysis."""
    baseline_passed: bool
    post_passed: bool
    regression_detected: bool
    details: str = ""


def check_regression(baseline_exit_code: int, post_exit_code: int) -> RegressionResult:
    """Determine whether the agent broke pre-existing tests.

    A regression is defined as: baseline passed (exit_code == 0) AND post-run failed (exit_code != 0).
    """
    baseline_passed = (baseline_exit_code == 0)
    post_passed = (post_exit_code == 0)
    regression_detected = baseline_passed and (not post_passed)

    details = ""
    if regression_detected:
        details = "Agent modifications broke pre-existing passing tests."
    elif not baseline_passed:
        details = "Baseline tests were already failing prior to harness execution."
    else:
        details = "No regressions detected."

    return RegressionResult(
        baseline_passed=baseline_passed,
        post_passed=post_passed,
        regression_detected=regression_detected,
        details=details,
    )
