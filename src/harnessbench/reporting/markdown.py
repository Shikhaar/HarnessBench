"""Markdown report generation for LEADERBOARD.md and results presentation."""

from typing import Dict, List, Optional
from harnessbench.models import BenchmarkManifest, RunResult
from harnessbench.reporting.json_report import calculate_awards, generate_benchmark_summary


def generate_markdown_report(
    runs: List[RunResult],
    model: str,
    manifest: Optional[BenchmarkManifest] = None,
) -> str:
    """Generate official LEADERBOARD.md with metrics, awards, and category breakdowns."""
    summary = generate_benchmark_summary(runs)
    awards = calculate_awards(summary)

    lines = [
        "# HarnessBench v0.1 — Experimental Leaderboard",
        "",
        "> **Notice:** This is an experimental benchmarking suite evaluating AI coding-agent harnesses holding the underlying LLM strictly constant.",
        "",
        f"**Model Tested:** `{model}`  ",
        f"**Total Executions:** {len(runs)}  ",
    ]

    if manifest:
        lines.append(f"**Repetitions per Task:** {manifest.repetitions}  ")
        lines.append(f"**Benchmark Timestamp:** `{manifest.timestamp}`  ")
        lines.append(f"**Commit:** `{manifest.git_commit or 'HEAD'}`  ")

    lines.extend([
        "",
        "## 🏆 Category Awards",
        "",
        "| Award | Winner | Metric Highlight |",
        "| :--- | :--- | :--- |",
    ])

    for award_name, winner in awards.items():
        w_stats = summary.get(winner, {})
        if award_name == "Highest Success Rate":
            metric_val = f"{w_stats.get('pass_rate', 0) * 100:.1f}% Pass Rate"
        elif award_name == "Most Cost Efficient":
            metric_val = f"${w_stats.get('cost_per_successful_task', 0):.4f} / successful task"
        elif award_name == "Fastest Latency":
            metric_val = f"{w_stats.get('latency_median_seconds', 0):.1f}s median latency"
        elif award_name == "Cleanest Repository":
            metric_val = f"{w_stats.get('total_pollution_score', 0)} total pollution score"
        elif award_name == "Lowest Regression Rate":
            metric_val = f"{w_stats.get('regression_rate', 0) * 100:.1f}% regression rate"
        else:
            metric_val = "-"

        lines.append(f"| **{award_name}** | **`{winner}`** | {metric_val} |")

    lines.extend([
        "",
        "## 📊 Main Leaderboard Rankings",
        "",
        "| Rank | Harness | Success Rate | Cost / Succ. Task | Median Latency | Tokens / Succ. Task | Regression Rate | Total Pollution |",
        "| :---: | :--- | :---: | :---: | :---: | :---: | :---: | :---: |",
    ])

    sorted_harnesses = sorted(
        summary.items(),
        key=lambda item: (item[1]["pass_rate"], -item[1]["cost_per_successful_task"]),
        reverse=True,
    )

    rank = 1
    for harness, s in sorted_harnesses:
        pass_str = f"**{s['pass_rate'] * 100:.1f}%** ({s['tasks_passed']}/{s['total_runs']})"
        cost_succ = f"${s['cost_per_successful_task']:.4f}" if s["tasks_passed"] > 0 else "N/A"
        tok_succ = f"{s['tokens_per_successful_task']:,}" if s["tasks_passed"] > 0 else "N/A"
        lat_str = f"{s['latency_median_seconds']:.1f}s"
        reg_str = f"{s['regression_rate'] * 100:.1f}%"
        poll_str = str(s["total_pollution_score"])

        lines.append(
            f"| #{rank} | **{harness}** | {pass_str} | {cost_succ} | {lat_str} | {tok_succ} | {reg_str} | {poll_str} |"
        )
        rank += 1

    # Breakdown by Language
    lines.extend([
        "",
        "## 🌐 Language Breakdown (Success Rate)",
        "",
        "| Harness | Python | TypeScript | Go | Java |",
        "| :--- | :---: | :---: | :---: | :---: |",
    ])

    for harness, s in sorted_harnesses:
        lb = s.get("language_breakdown", {})
        py_s = f"{lb.get('python', 0) * 100:.0f}%" if "python" in lb else "-"
        ts_s = f"{lb.get('typescript', 0) * 100:.0f}%" if "typescript" in lb else "-"
        go_s = f"{lb.get('go', 0) * 100:.0f}%" if "go" in lb else "-"
        java_s = f"{lb.get('java', 0) * 100:.0f}%" if "java" in lb else "-"
        lines.append(f"| **{harness}** | {py_s} | {ts_s} | {go_s} | {java_s} |")

    # Breakdown by Engineering Category
    all_categories = sorted(list({cat for s in summary.values() for cat in s.get("category_breakdown", {}).keys()}))
    if all_categories:
        lines.extend([
            "",
            "## 🛠️ Software Engineering Capabilities Breakdown",
            "",
            "| Harness | " + " | ".join(cat.replace("_", " ").title() for cat in all_categories) + " |",
            "| :--- | " + " | ".join([":---:"] * len(all_categories)) + " |",
        ])

        for harness, s in sorted_harnesses:
            cb = s.get("category_breakdown", {})
            row = [f"{cb.get(cat, 0) * 100:.0f}%" if cat in cb else "-" for cat in all_categories]
            lines.append(f"| **{harness}** | " + " | ".join(row) + " |")

    lines.extend([
        "",
        "## 🔬 Reproducibility",
        "",
        "To reproduce these exact results locally:",
        "```bash",
        "harnessbench validate-tasks",
        f"harnessbench run --harnesses {','.join(summary.keys())} --tasks all --model {model}",
        "```",
        "",
        "Historical raw runs and manifests are preserved in `results/history/`.",
    ])

    return "\n".join(lines)
