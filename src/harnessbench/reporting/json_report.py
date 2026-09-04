"""JSON report exporter for benchmark runs."""

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List
from harnessbench import __version__
from harnessbench.models import BenchmarkReport, RunResult


def generate_benchmark_summary(runs: List[RunResult]) -> Dict[str, Dict]:
    """Compute aggregate summary dictionary for each harness."""
    summary: Dict[str, Dict] = {}
    for r in runs:
        if r.harness not in summary:
            summary[r.harness] = {
                "tasks_total": 0,
                "tasks_passed": 0,
                "pass_rate": 0.0,
                "total_cost_usd": 0.0,
                "total_input_tokens": 0,
                "total_output_tokens": 0,
                "total_cache_read_tokens": 0,
                "total_tokens": 0,
                "total_duration_seconds": 0.0,
                "total_pollution_score": 0,
                "total_regressions": 0,
            }
        s = summary[r.harness]
        s["tasks_total"] += 1
        if r.success:
            s["tasks_passed"] += 1
        s["total_cost_usd"] = round(s["total_cost_usd"] + r.cost_usd, 6)
        s["total_input_tokens"] += r.input_tokens
        s["total_output_tokens"] += r.output_tokens
        s["total_cache_read_tokens"] += r.cache_read_tokens
        s["total_tokens"] += r.total_tokens
        s["total_duration_seconds"] = round(s["total_duration_seconds"] + r.duration_seconds, 2)
        s["total_pollution_score"] += r.pollution_score
        if r.regression_detected:
            s["total_regressions"] += 1

    for h, s in summary.items():
        if s["tasks_total"] > 0:
            s["pass_rate"] = round(s["tasks_passed"] / s["tasks_total"], 4)

    return summary


def save_benchmark_report(
    runs: List[RunResult],
    model: str,
    output_path: Path,
    benchmark_id: str = "benchmark_run",
) -> BenchmarkReport:
    """Serialize the complete benchmark report to JSON."""
    summary = generate_benchmark_summary(runs)
    report = BenchmarkReport(
        benchmark_id=benchmark_id,
        timestamp=datetime.utcnow(),
        model=model,
        runs=runs,
        summary=summary,
    )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(report.model_dump_json(indent=2), encoding="utf-8")
    return report
