"""Typer-based CLI for HarnessBench cross-language AI coding agent benchmark."""

import json
import platform
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Optional

import typer
import uvicorn
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from harnessbench import __version__
from harnessbench.adapters import get_adapter, list_adapters
from harnessbench.execution.runner import BenchmarkRunner, get_current_git_commit
from harnessbench.models import BenchmarkManifest, BenchmarkReport, RunResult
from harnessbench.reporting.history import list_benchmark_history, save_immutable_run_history
from harnessbench.reporting.json_report import save_benchmark_report
from harnessbench.reporting.leaderboard import print_leaderboard
from harnessbench.reporting.markdown import generate_markdown_report
from harnessbench.tasks import get_task_by_id, load_all_tasks, validate_task
from harnessbench.telemetry.proxy import ProxyServer, app as proxy_app

app = typer.Typer(
    name="harnessbench",
    help="HarnessBench: Cross-Language AI Coding Agent Benchmark Framework",
    no_args_is_help=True,
)

# Ensure console supports utf-8 safely on Windows
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

console = Console(highlight=False)


@app.command()
def version():
    """Display HarnessBench version and environment info."""
    console.print(f"[bold cyan]HarnessBench[/bold cyan] version [green]{__version__}[/green]")
    console.print(f"Python: {sys.version.split()[0]} | OS: {platform.platform()}")


@app.command()
def harnesses():
    """List all available harness adapters."""
    table = Table(title="Available Harness Adapters", header_style="bold magenta")
    table.add_column("Harness", style="bold white")
    table.add_column("Command Template", style="dim")
    table.add_column("Runtime / Mode", style="cyan")

    available = list_adapters()
    for name in available:
        try:
            if name == "aider":
                cmd = "aider --message <prompt> --yes --no-git"
                runtime = "CLI / Python"
            elif name in ("claude", "claude_code"):
                cmd = "claude -p <prompt>"
                runtime = "Claude Code Headless CLI"
            elif name == "codeless":
                cmd = "codeless --permission-mode full_auto -p <prompt>"
                runtime = "Autonomous Agent CLI"
            elif name == "mock":
                cmd = "(Internal Reference Solver)"
                runtime = "Mock Runtime (Zero-Cost Local Testing)"
            else:
                cmd = "custom"
                runtime = "Custom Runtime"
            table.add_row(name, cmd, runtime)
        except Exception:
            pass

    console.print(table)


@app.command()
def tasks():
    """List all available benchmark tasks across all supported languages."""
    task_list = load_all_tasks()
    if not task_list:
        console.print("[yellow]No tasks found in tasks/ directory.[/yellow]")
        return

    table = Table(title="Cross-Language Benchmark Tasks", header_style="bold magenta")
    table.add_column("Task ID", style="bold cyan")
    table.add_column("Language", style="bold yellow")
    table.add_column("Category", style="green")
    table.add_column("Difficulty", style="dim")
    table.add_column("Evaluation Command", style="white")

    for t in task_list:
        cmd_str = " ".join(t.evaluation_command) if isinstance(t.evaluation_command, list) else t.evaluation_command
        table.add_row(t.id, t.language, t.category, t.difficulty, cmd_str)

    console.print(table)


@app.command()
def validate_tasks(
    tasks: str = typer.Option("all", "--tasks", "-t", help="Comma-separated list of task IDs, or 'all'"),
):
    """Validate task integrity: verify baseline passes, pre-fix eval fails, golden patch applies, and post-fix passes."""
    all_available = load_all_tasks()
    selected = []
    if tasks.strip().lower() == "all":
        selected = all_available
    else:
        req_ids = [tid.strip() for tid in tasks.split(",") if tid.strip()]
        for req_id in req_ids:
            t = get_task_by_id(req_id)
            if t:
                selected.append(t)
            else:
                console.print(f"[yellow]Warning: Task '{req_id}' not found.[/yellow]")

    if not selected:
        console.print("[red]No tasks selected for validation.[/red]")
        raise typer.Exit(code=1)

    console.print(f"[bold cyan]Validating {len(selected)} benchmark tasks...[/bold cyan]\n")

    table = Table(title="Task Validation Results", header_style="bold magenta")
    table.add_column("Task ID", style="bold white")
    table.add_column("Language", style="yellow")
    table.add_column("Baseline Pre", justify="center")
    table.add_column("Eval Pre (Fail)", justify="center")
    table.add_column("Patch Apply", justify="center")
    table.add_column("Eval Post (Pass)", justify="center")
    table.add_column("Regression Guard", justify="center")
    table.add_column("Status", justify="center")

    all_valid = True

    for t in selected:
        res = validate_task(t)
        if not res.valid:
            all_valid = False

        b_pre = "[green]PASS[/green]" if res.baseline_pre_passed else "[red]FAIL[/red]"
        e_pre = "[green]PASS (Failed)[/green]" if res.eval_pre_failed else "[red]FAIL (Passed)[/red]"
        patch = "[green]APPLIED[/green]" if res.golden_patch_applied else "[red]FAILED[/red]"
        e_post = "[green]PASS[/green]" if res.eval_post_passed else "[red]FAIL[/red]"
        reg = "[green]PASS[/green]" if res.baseline_post_passed else "[red]REGRESSION[/red]"
        status = "[bold green]VALID[/bold green]" if res.valid else "[bold red]INVALID[/bold red]"

        table.add_row(t.id, t.language, b_pre, e_pre, patch, e_post, reg, status)

    console.print(table)

    if not all_valid:
        console.print("\n[bold red]Task validation failed for one or more tasks.[/bold red]")
        raise typer.Exit(code=1)
    else:
        console.print("\n[bold green]All tasks successfully validated![/bold green]")


@app.command()
def run(
    harnesses: str = typer.Option("mock", "--harnesses", "-h", help="Comma-separated list of harnesses"),
    tasks: str = typer.Option("all", "--tasks", "-t", help="Task IDs or 'all'"),
    model: str = typer.Option("claude-3-5-sonnet-20241022", "--model", "-m", help="Model held constant"),
    repetitions: int = typer.Option(1, "--repetitions", "-r", help="Number of repetitions per task"),
    timeout: Optional[int] = typer.Option(None, "--timeout", help="Execution timeout per task in seconds"),
    output_dir: Path = typer.Option(Path("results"), "--output-dir", "-o", help="Output directory"),
    proxy_port: int = typer.Option(8088, "--proxy-port", help="Proxy port"),
    use_proxy: bool = typer.Option(True, "--proxy/--no-proxy", help="Enable local MITM telemetry proxy"),
):
    """Execute benchmark runs across selected agent harnesses with repeated executions."""
    harness_names = [h.strip() for h in harnesses.split(",") if h.strip()]
    if not harness_names:
        console.print("[red]Error: No harnesses specified.[/red]")
        raise typer.Exit(code=1)

    all_available = load_all_tasks()
    selected_tasks = []
    if tasks.strip().lower() == "all":
        selected_tasks = all_available
    else:
        req_ids = [tid.strip() for tid in tasks.split(",") if tid.strip()]
        for req_id in req_ids:
            t = get_task_by_id(req_id)
            if t:
                selected_tasks.append(t)
            else:
                console.print(f"[yellow]Warning: Task '{req_id}' not found, skipping.[/yellow]")

    if not selected_tasks:
        console.print("[red]Error: No valid tasks selected.[/red]")
        raise typer.Exit(code=1)

    console.print(
        f"[bold green]Starting HarnessBench Run[/bold green] | Model: [cyan]{model}[/cyan] | Harnesses: {harness_names} | Tasks: {len(selected_tasks)} | Repetitions: {repetitions}"
    )

    all_results: List[RunResult] = []

    proxy_server = None
    proxy_url = None
    if use_proxy:
        proxy_server = ProxyServer(port=proxy_port)
        proxy_server.start()
        proxy_url = proxy_server.base_url
        console.print(f"[dim]Network Interceptor Proxy active on {proxy_url}[/dim]")

    try:
        total_runs = len(harness_names) * len(selected_tasks) * repetitions
        current_run = 0

        for rep in range(1, repetitions + 1):
            for h_name in harness_names:
                try:
                    adapter = get_adapter(h_name)
                except Exception as e:
                    console.print(f"[red]Failed to load adapter '{h_name}': {e}[/red]")
                    continue

                for task in selected_tasks:
                    current_run += 1
                    console.print(f"[{current_run}/{total_runs}] [bold]{h_name}[/bold] on [cyan]{task.id}[/cyan] (Rep {rep}/{repetitions})...")
                    runner = BenchmarkRunner(
                        task=task,
                        adapter=adapter,
                        model=model,
                        repetition_index=rep,
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

    # Create Benchmark Manifest
    manifest = BenchmarkManifest(
        benchmark_version=__version__,
        task_suite_version=__version__,
        model=model,
        provider="anthropic" if "claude" in model.lower() else ("openai" if "gpt" in model.lower() else "custom"),
        repetitions=repetitions,
        harnesses={h: get_adapter(h).name for h in harness_names},
        environment={
            "os": platform.platform(),
            "python": sys.version.split()[0],
        },
        timestamp=datetime.utcnow().isoformat(),
        git_commit=get_current_git_commit(),
    )

    # 1. Save standard current presentation files
    report_json_path = output_dir / "benchmark_report.json"
    report_md_path = output_dir / "benchmark_report.md"
    leaderboard_md_path = Path("LEADERBOARD.md")

    report = save_benchmark_report(
        runs=all_results,
        model=model,
        output_path=report_json_path,
        manifest=manifest,
    )

    md_content = generate_markdown_report(runs=all_results, model=model, manifest=manifest)
    report_md_path.write_text(md_content, encoding="utf-8")
    leaderboard_md_path.write_text(md_content, encoding="utf-8")

    # 2. Save immutable run history under results/history/<timestamp>/
    history_dir = save_immutable_run_history(manifest=manifest, report=report)

    console.print(f"\n[bold green]Benchmark Complete![/bold green] Saved to [cyan]{output_dir}/[/cyan] and immutable history to [cyan]{history_dir}/[/cyan]")

    # 3. Print Rich Leaderboard
    print_leaderboard(all_results, console=console)


@app.command()
def leaderboard(
    report_path: Path = typer.Option(Path("results/benchmark_report.json"), "--report", "-r", help="Report path"),
):
    """Display the leaderboard from an existing benchmark report."""
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
def history():
    """List all historical benchmark runs preserved in results/history/."""
    runs = list_benchmark_history()
    if not runs:
        console.print("[yellow]No historical benchmark runs found in results/history/.[/yellow]")
        return

    table = Table(title="HarnessBench Immutable History", header_style="bold magenta")
    table.add_column("Timestamp", style="bold cyan")
    table.add_column("Model", style="white")
    table.add_column("Harnesses", style="yellow")
    table.add_column("Repetitions", justify="center")
    table.add_column("Directory", style="dim")

    for r in runs:
        table.add_row(
            r["timestamp"],
            r["model"],
            ", ".join(r["harnesses"]),
            str(r["repetitions"]),
            r["run_dir"],
        )

    console.print(table)


@app.command()
def serve_proxy(
    port: int = typer.Option(8088, "--port", "-p", help="Port to listen on"),
    host: str = typer.Option("127.0.0.1", "--host", help="Bind host"),
):
    """Run standalone network interceptor proxy."""
    console.print(f"[bold cyan]Starting HarnessBench Proxy on http://{host}:{port}...[/bold cyan]")
    uvicorn.run(proxy_app, host=host, port=port)


if __name__ == "__main__":
    app()
