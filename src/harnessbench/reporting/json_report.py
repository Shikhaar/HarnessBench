"""JSON report exporter and statistical aggregator for cross-language benchmark runs."""

import statistics
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
from harnessbench.models import BenchmarkManifest, BenchmarkReport, RunResult


def generate_benchmark_summary(runs: List[RunResult]) -> Dict[str, Dict]:
    """Compute aggregate statistical summary dictionary for each harness."""
    harness_runs: Dict[str, List[RunResult]] = {}
    for r in runs:
        harness_runs.setdefault(r.harness, []).append(r)

    summary: Dict[str, Dict] = {}

    for harness, h_list in harness_runs.items():
        total_runs = len(h_list)
        successful_runs = [r for r in h_list if r.success]
        passed_count = len(successful_runs)

        pass_rate = round(passed_count / total_runs, 4) if total_runs > 0 else 0.0

        durations = [r.duration_seconds for r in h_list]
        costs = [r.cost_usd for r in h_list]
        tokens = [r.total_tokens for r in h_list]
        pollutions = [r.pollution_score for r in h_list]
        regressions = sum(1 for r in h_list if r.regression_detected)

        total_cost = sum(costs)
        total_tokens = sum(tokens)
        total_in = sum(r.input_tokens for r in h_list)
        total_out = sum(r.output_tokens for r in h_list)
        total_cache_read = sum(r.cache_read_tokens for r in h_list)

        cost_per_succ = round(total_cost / passed_count, 4) if passed_count > 0 else 0.0
        tokens_per_succ = int(round(total_tokens / passed_count)) if passed_count > 0 else 0

        # Category Breakdown
        categories: Dict[str, List[bool]] = {}
        languages: Dict[str, List[bool]] = {}
        for r in h_list:
            categories.setdefault(r.category, []).append(r.success)
            languages.setdefault(r.language, []).append(r.success)

        cat_summary = {k: round(sum(1 for s in v if s) / len(v), 3) for k, v in categories.items()}
        lang_summary = {k: round(sum(1 for s in v if s) / len(v), 3) for k, v in languages.items()}

        summary[harness] = {
            "total_runs": total_runs,
            "tasks_passed": passed_count,
            "pass_rate": pass_rate,
            "pass_rate_stddev": round(statistics.stdev([1.0 if r.success else 0.0 for r in h_list]), 3) if total_runs > 1 else 0.0,
            "total_cost_usd": round(total_cost, 4),
            "cost_mean_usd": round(statistics.mean(costs), 4) if costs else 0.0,
            "cost_per_successful_task": cost_per_succ,
            "total_input_tokens": total_in,
            "total_output_tokens": total_out,
            "total_cache_read_tokens": total_cache_read,
            "total_tokens": total_tokens,
            "tokens_mean": int(round(statistics.mean(tokens))) if tokens else 0,
            "tokens_per_successful_task": tokens_per_succ,
            "latency_median_seconds": round(statistics.median(durations), 2) if durations else 0.0,
            "latency_mean_seconds": round(statistics.mean(durations), 2) if durations else 0.0,
            "total_pollution_score": sum(pollutions),
            "pollution_score_mean": round(statistics.mean(pollutions), 2) if pollutions else 0.0,
            "total_regressions": regressions,
            "regression_rate": round(regressions / total_runs, 3) if total_runs > 0 else 0.0,
            "category_breakdown": cat_summary,
            "language_breakdown": lang_summary,
        }

    return summary


def calculate_awards(summary: Dict[str, Dict]) -> Dict[str, str]:
    """Determine category award winners across harnesses."""
    awards = {}
    if not summary:
        return awards

    # Highest Success Rate
    best_pass = max(summary.items(), key=lambda x: (x[1]["pass_rate"], -x[1]["total_cost_usd"]))
    awards["Highest Success Rate"] = best_pass[0]

    # Most Cost Efficient
    succ_cost = [item for item in summary.items() if item[1]["tasks_passed"] > 0]
    if succ_cost:
        best_cost = min(succ_cost, key=lambda x: x[1]["cost_per_successful_task"])
        awards["Most Cost Efficient"] = best_cost[0]

    # Fastest (Lowest median latency)
    best_lat = min(summary.items(), key=lambda x: x[1]["latency_median_seconds"])
    awards["Fastest Latency"] = best_lat[0]

    # Cleanest Repository (Lowest pollution)
    best_poll = min(summary.items(), key=lambda x: x[1]["total_pollution_score"])
    awards["Cleanest Repository"] = best_poll[0]

    # Lowest Regression Rate
    best_reg = min(summary.items(), key=lambda x: x[1]["regression_rate"])
    awards["Lowest Regression Rate"] = best_reg[0]

    return awards


def save_benchmark_report(
    runs: List[RunResult],
    model: str,
    output_path: Path,
    manifest: Optional[BenchmarkManifest] = None,
    benchmark_id: str = "benchmark_run",
) -> BenchmarkReport:
    """Serialize the complete benchmark report to JSON."""
    summary = generate_benchmark_summary(runs)
    awards = calculate_awards(summary)
    report = BenchmarkReport(
        benchmark_id=benchmark_id,
        timestamp=datetime.utcnow(),
        model=model,
        manifest=manifest,
        runs=runs,
        summary=summary,
        awards=awards,
    )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(report.model_dump_json(indent=2), encoding="utf-8")
    return report
