"""Integration test running complete end-to-end benchmark pipeline."""

import json
from pathlib import Path
from harnessbench.adapters.mock import MockAdapter
from harnessbench.execution.runner import BenchmarkRunner
from harnessbench.reporting.json_report import save_benchmark_report
from harnessbench.reporting.leaderboard import render_leaderboard
from harnessbench.reporting.markdown import generate_markdown_report
from harnessbench.tasks import load_all_tasks


def test_end_to_end_benchmark_pipeline(tmp_path: Path):
    tasks = load_all_tasks()
    assert len(tasks) >= 3

    # Run mock adapter on first python task
    python_tasks = [t for t in tasks if t.language == "python"]
    task = python_tasks[0] if python_tasks else tasks[0]
    mock_adapter = MockAdapter(behavior="solve")

    output_dir = tmp_path / "results"
    runner = BenchmarkRunner(
        task=task,
        adapter=mock_adapter,
        model="claude-3-5-sonnet-20241022",
        output_dir=output_dir,
    )

    result = runner.run()
    assert result.success is True
    assert result.pre_existing_tests_passed is True
    assert result.post_tests_passed is True
    assert result.regression_detected is False

    # Verify JSON persistence
    saved_file = output_dir / f"{result.run_id}.json"
    assert saved_file.exists()
    loaded_data = json.loads(saved_file.read_text(encoding="utf-8"))
    assert loaded_data["run_id"] == result.run_id
    assert loaded_data["task_id"] == task.id

    # Verify aggregate reports
    report_json = output_dir / "benchmark_report.json"
    save_benchmark_report(
        runs=[result],
        model="claude-3-5-sonnet-20241022",
        output_path=report_json,
    )
    assert report_json.exists()

    md_report = generate_markdown_report(
        runs=[result],
        model="claude-3-5-sonnet-20241022",
    )
    assert "Leaderboard" in md_report and "HarnessBench" in md_report

    # Verify leaderboard table builds
    table = render_leaderboard([result])
    assert table is not None
