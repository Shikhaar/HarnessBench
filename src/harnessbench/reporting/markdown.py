"""Markdown report generation for LEADERBOARD.md and results presentation."""

from typing import List, Optional
from harnessbench.datasets.models import BenchmarkRecord
from harnessbench.datasets.registry import load_all_external_records
from harnessbench.models import BenchmarkManifest, RunResult
from harnessbench.reporting.json_report import calculate_awards, generate_benchmark_summary


def generate_markdown_report(
    runs: List[RunResult],
    model: str,
    manifest: Optional[BenchmarkManifest] = None,
    external_records: Optional[List[BenchmarkRecord]] = None,
) -> str:
    """Generate official LEADERBOARD.md with two strictly separated sections:
    1. HarnessBench Controlled Results
    2. External Benchmark Reference Data
    """
    summary = generate_benchmark_summary(runs)
    awards = calculate_awards(summary)

    lines = [
        "# HarnessBench v0.1 — Experimental Leaderboard",
        "",
        "> **Notice:** This benchmarking suite evaluates AI coding-agent harnesses holding the underlying LLM strictly constant. External benchmark reference data is strictly segregated in its own section below and never combined with controlled HarnessBench results.",
        "",
        "# HarnessBench Controlled Results",
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
        "## Category Awards",
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
        "## Main Leaderboard Rankings",
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
        "## Language Breakdown (Success Rate)",
        "",
        "| Harness | Python | TypeScript | Go | Java | Rust |",
        "| :--- | :---: | :---: | :---: | :---: | :---: |",
    ])

    for harness, s in sorted_harnesses:
        lb = s.get("language_breakdown", {})
        py_s = f"{lb.get('python', 0) * 100:.0f}%" if "python" in lb else "-"
        ts_s = f"{lb.get('typescript', 0) * 100:.0f}%" if "typescript" in lb else "-"
        go_s = f"{lb.get('go', 0) * 100:.0f}%" if "go" in lb else "-"
        java_s = f"{lb.get('java', 0) * 100:.0f}%" if "java" in lb else "-"
        rust_s = f"{lb.get('rust', 0) * 100:.0f}%" if "rust" in lb else "-"
        lines.append(f"| **{harness}** | {py_s} | {ts_s} | {go_s} | {java_s} | {rust_s} |")

    # Breakdown by Engineering Category
    all_categories = sorted(list({cat for s in summary.values() for cat in s.get("category_breakdown", {}).keys()}))
    if all_categories:
        lines.extend([
            "",
            "## Software Engineering Capabilities Breakdown",
            "",
            "| Harness | " + " | ".join(cat.replace("_", " ").title() for cat in all_categories) + " |",
            "| :--- | " + " | ".join([":---:"] * len(all_categories)) + " |",
        ])

        for harness, s in sorted_harnesses:
            cb = s.get("category_breakdown", {})
            row = [f"{cb.get(cat, 0) * 100:.0f}%" if cat in cb else "-" for cat in all_categories]
            lines.append(f"| **{harness}** | " + " | ".join(row) + " |")

    # External Benchmark Reference Data Section (Strictly Separated)
    ext_records = external_records if external_records is not None else load_all_external_records()
    lines.extend([
        "",
        "---",
        "",
        "# External Benchmark Reference Data",
        "",
        "> **Methodological Separation:** These results were measured by third-party benchmarks under different experimental protocols. They are provided solely for contextual reference and must not be directly ranked against controlled HarnessBench runs.",
        "",
        "| Benchmark | Version | Model | Harness | Language | Result / Score | Cost ($) | Runtime (s) | Source | Retrieved |",
        "| :--- | :--- | :--- | :--- | :---: | :---: | :---: | :---: | :--- | :---: |",
    ])

    if not ext_records:
        lines.append("| - | - | - | - | - | - | - | - | No external benchmarks fetched yet | - |")
    else:
        for rec in ext_records:
            score_str = f"{rec.score * 100:.1f}%" if rec.score is not None else ("Passed" if rec.success else "Failed")
            cost_str = f"${rec.cost_usd:.4f}" if rec.cost_usd is not None else "-"
            time_str = f"{rec.runtime_seconds:.1f}s" if rec.runtime_seconds is not None else "-"
            lang_str = rec.language.capitalize() if rec.language else "-"
            model_str = rec.model_id or "-"
            harness_str = rec.harness or "-"
            b_name = rec.benchmark_name
            b_ver = rec.benchmark_version or "-"
            src_url = rec.provenance.source_url
            ret_date = rec.provenance.retrieved_at.strftime("%Y-%m-%d")
            lines.append(
                f"| {b_name} | {b_ver} | `{model_str}` | **{harness_str}** | {lang_str} | {score_str} | {cost_str} | {time_str} | [{b_name}]({src_url}) | {ret_date} |"
            )

    lines.extend([
        "",
        "## Reproducibility",
        "",
        "To reproduce controlled HarnessBench executions locally:",
        "```bash",
        "harnessbench validate-tasks",
        f"harnessbench run --harnesses {','.join(summary.keys()) or 'mock'} --tasks all --model {model}",
        "```",
        "",
        "To fetch official external benchmark reference datasets:",
        "```bash",
        "harnessbench dataset list",
        "harnessbench dataset fetch aider-polyglot",
        "harnessbench dataset fetch swebench",
        "harnessbench dataset fetch openhands",
        "```",
        "",
        "Historical controlled runs are preserved in `results/harnessbench/` and external data in `results/external/`.",
    ])

    return "\n".join(lines)
