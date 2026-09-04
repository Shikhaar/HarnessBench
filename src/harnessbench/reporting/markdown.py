"""Markdown report generation for CI/CD and READMEs."""

from typing import List
from harnessbench.models import RunResult
from harnessbench.reporting.json_report import generate_benchmark_summary


def generate_markdown_report(runs: List[RunResult], model: str) -> str:
    """Generate a GitHub-flavored Markdown leaderboard and breakdown."""
    summary = generate_benchmark_summary(runs)

    lines = [
        "# HarnessBench Leaderboard",
        "",
        f"**Model:** `{model}`  ",
        f"**Total Runs:** {len(runs)}  ",
        "",
        "| Harness | Pass Rate | Total Cost ($) | Tokens (In / Out) | Cache Read | Latency | Pollution | Regressions |",
        "| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |",
    ]

    for harness, s in sorted(summary.items(), key=lambda item: item[1]["pass_rate"], reverse=True):
        pass_str = f"{s['tasks_passed']}/{s['tasks_total']} ({s['pass_rate'] * 100:.1f}%)"
        cost_str = f"${s['total_cost_usd']:.4f}"
        token_str = f"{s['total_input_tokens']:,} / {s['total_output_tokens']:,}"
        cache_str = f"{s['total_cache_read_tokens']:,}"
        dur_str = f"{s['total_duration_seconds']:.1f}s"
        lines.append(
            f"| **{harness}** | {pass_str} | {cost_str} | {token_str} | {cache_str} | {dur_str} | {s['total_pollution_score']} | {s['total_regressions']} |"
        )

    lines.append("")
    lines.append("## Task-by-Task Details")
    lines.append("")
    lines.append("| Task ID | Harness | Success | Cost | Tokens | Duration | Pollution | Diff (Files/Lines) |")
    lines.append("| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: |")

    for r in runs:
        succ_mark = "✅ Pass" if r.success else "❌ Fail"
        cost_str = f"${r.cost_usd:.4f}"
        diff_str = f"{r.files_changed}f (+{r.lines_added}/-{r.lines_deleted})"
        lines.append(
            f"| `{r.task_id}` | {r.harness} | {succ_mark} | {cost_str} | {r.total_tokens:,} | {r.duration_seconds:.1f}s | {r.pollution_score} | {diff_str} |"
        )

    return "\n".join(lines)
