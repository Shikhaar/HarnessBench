"""Tests for BenchmarkRunner execution, budget limits, status classification, and persistence."""

from pathlib import Path
from harnessbench.adapters.mock import MockAdapter
from harnessbench.execution.runner import BenchmarkRunner, create_skipped_result
from harnessbench.models import BenchmarkTask


def test_runner_budget_skip_behavior(tmp_path: Path):
    task = BenchmarkTask(
        id="dummy_task",
        name="Dummy Task",
        language="python",
        category="bug_fixing",
        evaluation_command="pytest",
        baseline_command="pytest",
    )
    res = create_skipped_result(
        task=task,
        harness_name="mock",
        model="claude-3-5-sonnet-20241022",
        reason="skipped_budget_exceeded",
        output_dir=tmp_path,
    )
    assert res.budget_exceeded is True
    assert res.status == "skipped_budget_exceeded"
    assert res.success is False
    assert (tmp_path / f"{res.run_id}.json").exists()


def test_runner_timeout_classification(tmp_path: Path):
    task = BenchmarkTask(
        id="dummy_timeout",
        name="Dummy Timeout Task",
        language="python",
        category="concurrency",
        evaluation_command="python -c 'exit(0)'",
        baseline_command="python -c 'exit(0)'",
    )
    adapter = MockAdapter(timeout=True)
    runner = BenchmarkRunner(
        task=task,
        adapter=adapter,
        output_dir=tmp_path,
    )
    res = runner.run()
    assert res.timeout is True
    assert res.status == "timeout"
    assert res.success is False


def test_runner_harness_failed_classification(tmp_path: Path):
    task = BenchmarkTask(
        id="dummy_failure",
        name="Dummy Failure Task",
        language="python",
        category="bug_fixing",
        evaluation_command="python -c 'exit(1)'",
        baseline_command="python -c 'exit(0)'",
    )
    adapter = MockAdapter(fail=True)
    runner = BenchmarkRunner(
        task=task,
        adapter=adapter,
        output_dir=tmp_path,
    )
    res = runner.run()
    assert res.status == "harness_failed"
    assert res.harness_exit_code == 1
    assert res.success is False
