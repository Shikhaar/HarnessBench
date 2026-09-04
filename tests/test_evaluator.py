"""Tests for regression analysis and evaluation test orchestration."""

from harnessbench.evaluation.regression import check_regression


def test_regression_detected():
    # Baseline passed (0), post run failed (1)
    res = check_regression(baseline_exit_code=0, post_exit_code=1)
    assert res.baseline_passed is True
    assert res.post_passed is False
    assert res.regression_detected is True


def test_no_regression_when_both_pass():
    res = check_regression(baseline_exit_code=0, post_exit_code=0)
    assert res.baseline_passed is True
    assert res.post_passed is True
    assert res.regression_detected is False


def test_no_regression_when_baseline_already_failed():
    res = check_regression(baseline_exit_code=1, post_exit_code=1)
    assert res.baseline_passed is False
    assert res.regression_detected is False
