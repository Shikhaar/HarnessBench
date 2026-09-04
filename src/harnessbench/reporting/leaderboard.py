"""Rich terminal leaderboard table generation."""

from typing import Dict, List
from rich.console import Console
from rich.table import Table
from harnessbench.models import RunResult


def render_leaderboard(results: List[RunResult], console: Console = None) -> Table:
    """Render a clean Rich terminal table summarizing benchmark results by harness."""
    if console is None:
        console = Console()

    table = Table(
        title="[bold cyan]HarnessBench — Coding Agent Harness Leaderboard[/bold cyan]",
        header_style="bold magenta",
        show_lines=True,
    )

    table.add_column("Harness", style="bold white", justify="left")
    table.add_column("Model", style="dim", justify="left")
    table.add_column("Pass Rate", justify="center")
    table.add_column("Total Cost", justify="right")
    table.add_column("Tokens (In/Out)", justify="right")
    table.add_column("Cache Read", justify="right")
    table.add_column("Turns", justify="center")
    table.add_column("Latency", justify="right")
    table.add_column("Pollution", justify="center")
    table.add_column("Regressions", justify="center")

    # Group runs by harness
    harness_groups: Dict[str, List[RunResult]] = {}
    for r in results:
        harness_groups.setdefault(r.harness, []).append(r)

    # Sort harnesses by pass rate descending, then cost ascending
    sorted_harnesses = sorted(
        harness_groups.keys(),
        key=lambda h: (
            sum(1 for r in harness_groups[h] if r.success) / max(len(harness_groups[h]), 1),
            -sum(r.cost_usd for r in harness_groups[h]),
        ),
        reverse=True,
    )

    for harness_name in sorted_harnesses:
        runs = harness_groups[harness_name]
        total_tasks = len(runs)
        passed_tasks = sum(1 for r in runs if r.success)
        total_cost = sum(r.cost_usd for r in runs)
        total_in = sum(r.input_tokens for r in runs)
        total_out = sum(r.output_tokens for r in runs)
        total_cache = sum(r.cache_read_tokens for r in runs)
        total_turns = sum(r.turn_count for r in runs)
        total_duration = sum(r.duration_seconds for r in runs)
        total_pollution = sum(r.pollution_score for r in runs)
        total_regressions = sum(1 for r in runs if r.regression_detected)
        model_name = runs[0].model if runs else ""

        # Color-coded pass rate
        pass_color = "green" if passed_tasks == total_tasks else ("yellow" if passed_tasks > 0 else "red")
        pass_str = f"[{pass_color}]{passed_tasks}/{total_tasks}[/{pass_color}]"

        pollution_str = f"[red]{total_pollution}[/red]" if total_pollution > 0 else "[green]0[/green]"
        regression_str = f"[red]{total_regressions}[/red]" if total_regressions > 0 else "[green]0[/green]"

        table.add_row(
            harness_name,
            model_name,
            pass_str,
            f"${total_cost:.4f}",
            f"{total_in:,} / {total_out:,}",
            f"{total_cache:,}",
            str(total_turns),
            f"{total_duration:.1f}s",
            pollution_str,
            regression_str,
        )

    return table


def print_leaderboard(results: List[RunResult], console: Console = None) -> None:
    """Print the formatted leaderboard table to the console."""
    if console is None:
        console = Console()
    table = render_leaderboard(results, console=console)
    console.print()
    console.print(table)
    console.print()
