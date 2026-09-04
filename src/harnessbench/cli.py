"""Typer-based CLI for HarnessBench."""

import json
from pathlib import Path
from typing import List, Optional

import typer
import uvicorn
from rich.console import Console
from rich.table import Table

from harnessbench import __version__
from harnessbench.adapters import get_adapter, list_adapters
from harnessbench.execution.runner import BenchmarkRunner
from harnessbench.models import BenchmarkReport, RunResult
from harnessbench.reporting.json_report import save_benchmark_report
from harnessbench.reporting.leaderboard import print_leaderboard
from harnessbench.reporting.markdown import generate_markdown_report
from harnessbench.tasks import get_task_by_id, load_all_tasks
from harnessbench.telemetry.proxy import ProxyServer, app as proxy_app

app = typer.Typer(
    name="harnessbench",
    help="HarnessBench: AI Coding Agent Harness Benchmarking Framework",
    no_args_is_help=True,
)
console = Console()


@app.command()
def version():
    """Display HarnessBench version."""
    console.print(f"[bold cyan]HarnessBench[/bold cyan] version [green]{__version__}[/green]")


@app.command()
def harnesses():
    """List all available harness adapters."""
    table = Table(title="Available Harness Adapters", header_style="bold magenta")
    table.add_column("Harness Name", style="bold white")
    table.add_column("Command Template", style="dim")
    table.add_column("Target Runtime", style="cyan")

    available = list_adapters()
    for name in available:
        try:
            adapter = get_adapter(name)
            if name == "aider":
                cmd = "aider --message <prompt> --yes --no-git"
                runtime = "CLI / Python"
            elif name in ("claude", "claude_code"):
                cmd = "claude -p <prompt>"
                runtime = "Claude Code CLI"
            elif name == "codeless":
                cmd = "codeless --permission-mode full_auto -p <prompt>"
                runtime = "Autonomous Agent CLI"
            elif name == "mock":
                cmd = "(Internal Mock / Reference Solver)"
                runtime = "Mock Runtime (Zero-Cost Testing)"
            else:
                cmd = "custom"
                runtime = "Unknown"
            table.add_row(name, cmd, runtime)
        except Exception:
            pass

    console.print(table)


@app.command()
def tasks():
    """List all available benchmark tasks."""
    task_list = load_all_tasks()
    if not task_list:
        console.print("[yellow]No tasks found in tasks/ directory.[/yellow]")
        return

    table = Table(title="Benchmark Tasks", header_style="bold magenta")
    table.add_column("Task ID", style="bold cyan")
    table.add_column("Name", style="bold white")
    table.add_column("Description", style="dim")
    table.add_column("Expected Files", style="green")

    for t in task_list:
        exp_str = ", ".join(t.expected_files) if t.expected_files else "(none specified)"
        table.add_row(t.id, t.name, t.description, exp_str)

    console.print(table)


@app.command()
def run(
    harnesses: str = typer.Option(
        "mock",
        "--harnesses",
        "-h",
        help="Comma-separated list of harnesses to benchmark (e.g. aider,claude,codeless,mock)",
    ),
    tasks: str = typer.Option(
        "all",
        "--tasks",
        "-t",
        help="Comma-separated list of task IDs to run, or 'all'",
    ),
    model: str = typer.Option(
        "claude-3-5-sonnet-20241022",
        "--model",
        "-m",
        help="Model identifier held constant across harnesses",
    ),
    timeout: int = typer.Option(
        300,
        "--timeout",
        help="Execution timeout per task in seconds",
    ),
    output_dir: Path = typer.Option(
        Path("results"),
        "--output-dir",
        "-o",
        help="Directory to save run results and benchmark report",
    ),
    proxy_port: int = typer.Option(
        8088,
        "--proxy-port",
        help="Local port for telemetry interceptor proxy",
    ),
    use_proxy: bool = typer.Option(
        True,
        "--proxy/--no-proxy",
        help="Enable/disable local MITM telemetry proxy",
    ),
):
    """Execute benchmark tasks across selected agent harnesses."""
    # 1. Parse selected harnesses
    harness_names = [h.strip() for h in harnesses.split(",") if h.strip()]
    if not harness_names:
        console.print("[red]Error:[/red] No harnesses specified.")
        raise typer.Exit(code=1)

    # 2. Parse selected tasks
    all_available_tasks = load_all_tasks()
    selected_tasks = []
    if tasks.strip().lower() == "all":
        selected_tasks = all_available_tasks
    else:
        req_ids = [tid.strip() for tid in tasks.split(",") if tid.strip()]
        for req_id in req_ids:
            t = get_task_by_id(req_id)
            if t:
                selected_tasks.append(t)
            else:
                console.print(f"[yellow]Warning: Task '{req_id}' not found, skipping.[/yellow]")

    if not selected_tasks:
        console.print("[red]Error:[/red] No valid tasks selected to run.")
        raise typer.Exit(code=1)

    console.print(
        f"[bold green]Starting HarnessBench Run[/bold green] | Model: [cyan]{model}[/cyan] | Harnesses: {harness_names} | Tasks: {len(selected_tasks)}"
    )

    all_results: List[RunResult] = []

    # 3. Start proxy if enabled
    proxy_server = None
    proxy_url = None
    if use_proxy:
        proxy_server = ProxyServer(port=proxy_port)
        proxy_server.start()
        proxy_url = proxy_server.base_url
        console.print(f"[dim]Network Interceptor Proxy active on {proxy_url}[/dim]")

    try:
        total_runs = len(harness_names) * len(selected_tasks)
        current_run = 0

        for h_name in harness_names:
            try:
                adapter = get_adapter(h_name)
            except Exception as e:
                console.print(f"[red]Failed to load adapter '{h_name}': {e}[/red]")
                continue

            for task in selected_tasks:
                current_run += 1
                console.print(f"[{current_run}/{total_runs}] Running [bold]{h_name}[/bold] on [cyan]{task.id}[/cyan]...")
                runner = BenchmarkRunner(
                    task=task,
                    adapter=adapter,
                    model=model,
                    proxy_url=proxy_url,
                    timeout=timeout,
                    output_dir=output_dir,
                )
                res = runner.run()
                all_results.append(res)
                status_str = "[green]PASSED[/green]" if res.success else "[red]FAILED[/red]"
                console.print(
                    f"     Outcome: {status_str} | Cost: ${res.cost_usd:.4f} | Time: {res.duration_seconds:.1f}s | Pollution: {res.pollution_score}"
                )

    finally:
        if proxy_server:
            proxy_server.stop()

    # 4. Generate aggregate report & Markdown
    report_json_path = output_dir / "benchmark_report.json"
    report_md_path = output_dir / "benchmark_report.md"

    save_benchmark_report(runs=all_results, model=model, output_path=report_json_path)

    md_content = generate_markdown_report(runs=all_results, model=model)
    report_md_path.write_text(md_content, encoding="utf-8")

    console.print(f"\n[bold green]Benchmark Complete![/bold green] Results saved to [cyan]{output_dir}/[/cyan]")

    # 5. Render Leaderboard
    print_leaderboard(all_results, console=console)


@app.command()
def leaderboard(
    report_path: Path = typer.Option(
        Path("results/benchmark_report.json"),
        "--report",
        "-r",
        help="Path to benchmark_report.json",
    ),
):
    """Display the leaderboard from a previous benchmark run."""
    if not report_path.exists():
        console.print(f"[red]Report file not found:[/red] {report_path}")
        raise typer.Exit(code=1)

    try:
        data = json.loads(report_path.read_text(encoding="utf-8"))
        report = BenchmarkReport.model_validate(data)
        print_leaderboard(report.runs, console=console)
    except Exception as e:
        console.print(f"[red]Failed to load report:[/red] {e}")
        raise typer.Exit(code=1)


@app.command()
def serve_proxy(
    port: int = typer.Option(8088, "--port", "-p", help="Port to listen on"),
    host: str = typer.Option("127.0.0.1", "--host", help="Bind host"),
):
    """Run the standalone network telemetry interceptor proxy."""
    console.print(f"[bold cyan]Starting HarnessBench Proxy on http://{host}:{port}...[/bold cyan]")
    uvicorn.run(proxy_app, host=host, port=port)


if __name__ == "__main__":
    app()
