"""Rich terminal leaderboard generation with statistical aggregation, awards, and external reference tables."""

from typing import Dict, List, Optional
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from harnessbench.datasets.models import BenchmarkRecord
from harnessbench.datasets.registry import load_all_external_records
from harnessbench.models import RunResult
from harnessbench.reporting.json_report import calculate_awards, generate_benchmark_summary


def render_leaderboard(results: List[RunResult], console: Optional[Console] = None) -> Table:
    """Render a clean Rich terminal table summarizing controlled HarnessBench results by harness."""
    if console is None:
        console = Console()

    summary = generate_benchmark_summary(results)

    table = Table(
        title="[bold cyan]HarnessBench — Controlled Benchmark Results[/bold cyan]",
        header_style="bold magenta",
        show_lines=True,
    )

    table.add_column("Rank", justify="center", style="bold yellow")
    table.add_column("Harness", style="bold white", justify="left")
    table.add_column("Success Rate", justify="center")
    table.add_column("Cost / Succ.", justify="right", style="green")
    table.add_column("Median Latency", justify="right")
    table.add_column("Tokens (In/Out)", justify="right")
    table.add_column("Cache Read", justify="right")
    table.add_column("Pollution", justify="center")
    table.add_column("Regressions", justify="center")

    sorted_harnesses = sorted(
        summary.items(),
        key=lambda item: (item[1]["pass_rate"], -item[1]["cost_per_successful_task"]),
        reverse=True,
    )

    rank = 1
    for harness_name, s in sorted_harnesses:
        pass_pct = s["pass_rate"] * 100
        pass_color = "green" if pass_pct >= 80 else ("yellow" if pass_pct >= 50 else "red")
        if s["total_runs"] > s["tasks_passed"] and s["pass_rate_stddev"] > 0:
            pass_str = f"[{pass_color}]{pass_pct:.1f}% ±{s['pass_rate_stddev']*100:.1f}%[/{pass_color}] ({s['tasks_passed']}/{s['total_runs']})"
        else:
            pass_str = f"[{pass_color}]{pass_pct:.1f}%[/{pass_color}] ({s['tasks_passed']}/{s['total_runs']})"

        cost_succ = f"${s['cost_per_successful_task']:.4f}" if s["tasks_passed"] > 0 else "N/A"
        lat_str = f"{s['latency_median_seconds']:.1f}s"
        tok_str = f"{s['total_input_tokens']:,} / {s['total_output_tokens']:,}"
        cache_str = f"{s['total_cache_read_tokens']:,}"
        poll_color = "red" if s["total_pollution_score"] > 0 else "green"
        poll_str = f"[{poll_color}]{s['total_pollution_score']}[/{poll_color}]"
        reg_color = "red" if s["total_regressions"] > 0 else "green"
        reg_str = f"[{reg_color}]{s['total_regressions']}[/{reg_color}]"

        table.add_row(
            f"#{rank}",
            harness_name,
            pass_str,
            cost_succ,
            lat_str,
            tok_str,
            cache_str,
            poll_str,
            reg_str,
        )
        rank += 1

    return table


def render_external_benchmarks_table(records: List[BenchmarkRecord]) -> Table:
    """Render external reference benchmark data in a distinct, unranked table with provenance."""
    table = Table(
        title="[bold yellow]External Benchmark Reference Data (Third-Party Protocols)[/bold yellow]",
        header_style="bold cyan",
        show_lines=True,
    )

    table.add_column("Benchmark", style="bold white")
    table.add_column("Version", style="dim")
    table.add_column("Model", style="yellow")
    table.add_column("Harness / Agent", style="magenta")
    table.add_column("Language", justify="center")
    table.add_column("Result / Score", justify="center", style="green")
    table.add_column("Cost ($)", justify="right")
    table.add_column("Runtime (s)", justify="right")
    table.add_column("Retrieved", justify="center", style="dim")

    for rec in records:
        score_str = f"{rec.score * 100:.1f}%" if rec.score is not None else ("PASS" if rec.success else "FAIL")
        cost_str = f"${rec.cost_usd:.4f}" if rec.cost_usd is not None else "N/A"
        time_str = f"{rec.runtime_seconds:.1f}s" if rec.runtime_seconds is not None else "N/A"
        lang_str = rec.language.capitalize() if rec.language else "-"
        ret_date = rec.provenance.retrieved_at.strftime("%Y-%m-%d")

        table.add_row(
            rec.benchmark_name,
            rec.benchmark_version or "-",
            rec.model_id or "-",
            rec.harness or "-",
            lang_str,
            score_str,
            cost_str,
            time_str,
            ret_date,
        )

    return table


def print_leaderboard(
    results: List[RunResult],
    external_records: Optional[List[BenchmarkRecord]] = None,
    console: Optional[Console] = None,
) -> None:
    """Print the formatted leaderboard, awards, and separate external reference data to console."""
    if console is None:
        console = Console()

    summary = generate_benchmark_summary(results)
    awards = calculate_awards(summary)

    console.print()
    console.print(render_leaderboard(results, console=console))

    if awards:
        awards_table = Table(title="[bold yellow][Awards] Category Awards[/bold yellow]", header_style="bold cyan")
        awards_table.add_column("Award", style="bold white")
        awards_table.add_column("Winner", style="bold green")
        for award, winner in awards.items():
            awards_table.add_row(award, winner)
        console.print(awards_table)

    # Display external benchmark references separately
    ext = external_records if external_records is not None else load_all_external_records()
    if ext:
        console.print()
        console.print(render_external_benchmarks_table(ext))

    console.print()
