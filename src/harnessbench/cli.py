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
from rich.table import Table

from harnessbench import __version__
from harnessbench.adapters import get_adapter, list_adapters
from harnessbench.datasets.registry import (
    fetch_and_save_dataset,
    list_adapters as list_dataset_adapters,
    list_dataset_names,
    load_all_external_records,
)
from harnessbench.execution.runner import (
    BenchmarkRunner,
    create_skipped_result,
    get_current_git_commit,
)
from harnessbench.models import BenchmarkManifest, BenchmarkReport, RunResult
from harnessbench.reporting.history import list_benchmark_history, save_immutable_run_history
from harnessbench.reporting.json_report import save_benchmark_report
from harnessbench.reporting.leaderboard import print_leaderboard, render_external_benchmarks_table, render_leaderboard
from harnessbench.reporting.markdown import generate_markdown_report
from harnessbench.tasks import get_task_by_id, load_all_tasks, validate_task
from harnessbench.telemetry.proxy import ProxyServer, app as proxy_app

app = typer.Typer(
    name="harnessbench",
    help="HarnessBench: Cross-Language AI Coding Agent Benchmark Framework",
    no_args_is_help=True,
)

dataset_app = typer.Typer(
    name="dataset",
    help="Ingest, query, and manage official external benchmark reference datasets.",
    no_args_is_help=True,
)
app.add_typer(dataset_app, name="dataset")

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
    table.add_column("Adapter Name", style="bold cyan")
    table.add_column("CLI Command", style="yellow")
    table.add_column("Runtime Environment", style="white")

    for name in list_adapters():
        try:
            ad = get_adapter(name)
            if hasattr(ad, "command"):
                cmd = " ".join(ad.command)
                runtime = "CLI Process Subprocess"
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

    has_invalid = False
    unavailable_count = 0

    for t in selected:
        res = validate_task(t)
        if not res.environment_available:
            unavailable_count += 1
            b_pre = "[dim]SKIP[/dim]"
            e_pre = "[dim]SKIP[/dim]"
            patch = "[dim]SKIP[/dim]"
            e_post = "[dim]SKIP[/dim]"
            reg = "[dim]SKIP[/dim]"
            status = "[bold yellow]ENV_UNAVAILABLE[/bold yellow]"
        else:
            if not res.valid:
                has_invalid = True
            b_pre = "[green]PASS[/green]" if res.baseline_pre_passed else "[red]FAIL[/red]"
            e_pre = "[green]PASS (Failed)[/green]" if res.eval_pre_failed else "[red]FAIL (Passed)[/red]"
            patch = "[green]APPLIED[/green]" if res.golden_patch_applied else "[red]FAILED[/red]"
            e_post = "[green]PASS[/green]" if res.eval_post_passed else "[red]FAIL[/red]"
            reg = "[green]PASS[/green]" if res.baseline_post_passed else "[red]REGRESSION[/red]"
            status = "[bold green]VALID[/bold green]" if res.valid else "[bold red]INVALID[/bold red]"

        table.add_row(t.id, t.language, b_pre, e_pre, patch, e_post, reg, status)

    console.print(table)

    if has_invalid:
        console.print("\n[bold red]Task validation failed for one or more tasks with available runtimes.[/bold red]")
        raise typer.Exit(code=1)
    else:
        if unavailable_count > 0:
            console.print(f"\n[bold green]All available tasks validated![/bold green] ([yellow]{unavailable_count} task(s) skipped due to missing environment runtime[/yellow])")
        else:
            console.print("\n[bold green]All tasks successfully validated![/bold green]")


@app.command()
def run(
    harnesses: str = typer.Option("mock", "--harnesses", "-h", help="Comma-separated list of harnesses"),
    tasks: str = typer.Option("all", "--tasks", "-t", help="Task IDs or 'all'"),
    model: str = typer.Option("claude-3-5-sonnet-20241022", "--model", "-m", help="Model held constant"),
    repetitions: int = typer.Option(1, "--repetitions", "-r", help="Number of repetitions per task"),
    timeout: Optional[int] = typer.Option(None, "--timeout", help="Execution timeout per task in seconds"),
    max_cost: Optional[float] = typer.Option(None, "--max-cost", help="Maximum aggregate USD cost budget"),
    max_runtime: Optional[float] = typer.Option(None, "--max-runtime", help="Maximum aggregate runtime in seconds"),
    output_dir: Path = typer.Option(Path("results"), "--output-dir", "-o", help="Output directory"),
    proxy_port: int = typer.Option(8088, "--proxy-port", help="Proxy port"),
    use_proxy: bool = typer.Option(True, "--proxy/--no-proxy", help="Enable local MITM telemetry proxy"),
):
    """Execute controlled benchmark runs across agent harnesses with budget guards."""
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

    budget_msg = f" | Max Cost: ${max_cost:.2f}" if max_cost is not None else ""
    runtime_msg = f" | Max Runtime: {max_runtime:.0f}s" if max_runtime is not None else ""
    console.print(
        f"[bold green]Starting HarnessBench Run[/bold green] | Model: [cyan]{model}[/cyan] | Harnesses: {harness_names} | Tasks: {len(selected_tasks)} | Repetitions: {repetitions}{budget_msg}{runtime_msg}"
    )

    all_results: List[RunResult] = []
    cumulative_cost = 0.0
    cumulative_runtime = 0.0

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

                    # Budget Guard: Check if cost or runtime limits reached
                    if max_cost is not None and cumulative_cost >= max_cost:
                        console.print(f"[{current_run}/{total_runs}] [bold]{h_name}[/bold] on [cyan]{task.id}[/cyan] [yellow]SKIPPED (Cost budget ${max_cost:.2f} reached)[/yellow]")
                        skipped = create_skipped_result(
                            task=task,
                            harness_name=h_name,
                            model=model,
                            repetition_index=rep,
                            reason="skipped_budget_exceeded",
                            output_dir=output_dir,
                        )
                        all_results.append(skipped)
                        continue

                    if max_runtime is not None and cumulative_runtime >= max_runtime:
                        console.print(f"[{current_run}/{total_runs}] [bold]{h_name}[/bold] on [cyan]{task.id}[/cyan] [yellow]SKIPPED (Runtime limit {max_runtime:.0f}s reached)[/yellow]")
                        skipped = create_skipped_result(
                            task=task,
                            harness_name=h_name,
                            model=model,
                            repetition_index=rep,
                            reason="timeout",
                            output_dir=output_dir,
                        )
                        all_results.append(skipped)
                        continue

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
                    cumulative_cost += res.cost_usd
                    cumulative_runtime += res.duration_seconds

                    if res.status == "passed":
                        status_str = "[green]PASSED[/green]"
                    elif res.status == "environment_unavailable":
                        status_str = "[yellow]ENV_UNAVAILABLE[/yellow]"
                    elif res.status == "timeout":
                        status_str = "[yellow]TIMEOUT[/yellow]"
                    else:
                        status_str = "[red]FAILED[/red]"

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

    # Load external records for separate reference display in LEADERBOARD.md
    ext_records = load_all_external_records()
    md_content = generate_markdown_report(runs=all_results, model=model, manifest=manifest, external_records=ext_records)
    report_md_path.write_text(md_content, encoding="utf-8")
    leaderboard_md_path.write_text(md_content, encoding="utf-8")

    # 2. Save immutable run history under results/harnessbench/<timestamp>/
    hb_history_dir = Path("results/harnessbench") / datetime.utcnow().strftime("%Y-%m-%dT%H-%M-%SZ")
    save_immutable_run_history(manifest=manifest, report=report, history_dir=hb_history_dir)
    # Also keep results/history for legacy backward compatibility
    save_immutable_run_history(manifest=manifest, report=report)

    console.print(f"\n[bold green]Benchmark Complete![/bold green] Saved to [cyan]{output_dir}/[/cyan] and immutable history to [cyan]{hb_history_dir}/[/cyan]")

    # 3. Print Rich Leaderboard
    print_leaderboard(all_results, external_records=ext_records, console=console)


@app.command()
def leaderboard(
    report_path: Path = typer.Option(Path("results/benchmark_report.json"), "--report", "-r", help="Report path"),
):
    """Display the leaderboard from an existing benchmark report and external reference datasets."""
    if not report_path.exists():
        console.print(f"[red]Report file not found:[/red] {report_path}")
        raise typer.Exit(code=1)

    try:
        data = json.loads(report_path.read_text(encoding="utf-8"))
        report = BenchmarkReport.model_validate(data)
        ext = load_all_external_records()
        print_leaderboard(report.runs, external_records=ext, console=console)
    except Exception as e:
        console.print(f"[red]Failed to load report:[/red] {e}")
        raise typer.Exit(code=1)


@app.command()
def history():
    """List all historical benchmark runs preserved in results/harnessbench/ and results/history/."""
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


# ==========================================
# Dataset Management Commands
# ==========================================

@dataset_app.command("list")
def dataset_list():
    """Display available official external benchmark reference datasets."""
    adapters = list_dataset_adapters()
    table = Table(title="External Benchmark Reference Datasets", header_style="bold magenta")
    table.add_column("Dataset Slug", style="bold cyan")
    table.add_column("Title", style="bold white")
    table.add_column("Languages", style="yellow")
    table.add_column("Tasks", justify="center")
    table.add_column("Version", style="dim")
    table.add_column("Last Updated", style="dim")
    table.add_column("License", style="green")

    for a in adapters:
        m = a.metadata()
        langs = ", ".join(m.languages) if m.languages else "all"
        t_count = str(m.task_count) if m.task_count else "-"
        table.add_row(m.name, m.display_name, langs, t_count, m.version or "-", m.last_updated or "-", m.license)

    console.print(table)


@dataset_app.command("fetch")
def dataset_fetch(
    name: str = typer.Argument(..., help="Dataset slug (aider-polyglot, swebench, openhands)"),
):
    """Fetch official external benchmark data, normalize schema, and store with provenance."""
    try:
        console.print(f"[bold cyan]Fetching official benchmark data for '{name}'...[/bold cyan]")
        meta, count, saved_path = fetch_and_save_dataset(name)
        console.print(f"[bold green]Successfully imported {count} records from '{meta.display_name}'![/bold green]")
        console.print(f"Source URL: [cyan]{meta.source_url}[/cyan]")
        console.print(f"Version: {meta.version or 'N/A'} | License: {meta.license}")
        console.print(f"Saved artifacts to: [dim]{saved_path}[/dim]")
    except Exception as e:
        console.print(f"[bold red]Failed to fetch dataset '{name}':[/bold red] {e}")
        raise typer.Exit(code=1)


@dataset_app.command("update")
def dataset_update():
    """Refresh all supported external reference benchmark datasets."""
    names = list_dataset_names()
    console.print(f"[bold cyan]Updating {len(names)} external benchmark reference datasets...[/bold cyan]\n")
    for name in names:
        try:
            meta, count, saved_path = fetch_and_save_dataset(name)
            console.print(f"[green]PASS[/green] Updated [bold]{meta.display_name}[/bold] ({count} records)")
        except Exception as e:
            console.print(f"[red]FAIL[/red] Failed to update '{name}': {e}")


# ==========================================
# Compare / Query Command
# ==========================================

@app.command()
def compare(
    source: Optional[str] = typer.Option(None, "--source", "-s", help="Filter by source: 'harnessbench' or 'external'"),
    harnesses: Optional[str] = typer.Option(None, "--harnesses", "-h", help="Comma-separated harness filter"),
    language: Optional[str] = typer.Option(None, "--language", "-l", help="Language filter"),
    category: Optional[str] = typer.Option(None, "--category", "-c", help="Category filter"),
    model: Optional[str] = typer.Option(None, "--model", "-m", help="Model filter"),
    benchmark: Optional[str] = typer.Option(None, "--benchmark", "-b", help="Benchmark name filter"),
):
    """Query and compare benchmark results with strict source isolation."""
    src_filter = source.strip().lower() if source else None
    if src_filter and src_filter not in ("harnessbench", "external"):
        console.print("[red]Error: --source must be either 'harnessbench' or 'external'.[/red]")
        raise typer.Exit(code=1)

    h_list = [h.strip().lower() for h in harnesses.split(",")] if harnesses else []

    # 1. Query Controlled HarnessBench runs
    if src_filter in (None, "harnessbench"):
        report_file = Path("results/benchmark_report.json")
        hb_runs = []
        if report_file.exists():
            try:
                rep_data = json.loads(report_file.read_text(encoding="utf-8"))
                for r_raw in rep_data.get("runs", []):
                    r = RunResult.model_validate(r_raw)
                    if h_list and r.harness.lower() not in h_list:
                        continue
                    if language and r.language.lower() != language.lower():
                        continue
                    if category and r.category.lower() != category.lower():
                        continue
                    if model and r.model.lower() != model.lower():
                        continue
                    hb_runs.append(r)
            except Exception:
                pass

        if hb_runs:
            console.print(render_leaderboard(hb_runs, console=console))
        elif src_filter == "harnessbench":
            console.print("[yellow]No controlled HarnessBench runs matched the specified filters.[/yellow]")

    # 2. Query External Reference benchmark records
    if src_filter in (None, "external"):
        ext_records = load_all_external_records()
        filtered_ext = []
        for rec in ext_records:
            clean_bench_filter = benchmark.lower().replace("-", " ").replace("_", " ") if benchmark else None
            clean_rec_bench = rec.benchmark_name.lower().replace("-", " ").replace("_", " ")
            if clean_bench_filter and clean_bench_filter not in clean_rec_bench:
                continue
            if h_list and rec.harness and rec.harness.lower() not in h_list:
                continue
            if language and rec.language and rec.language.lower() != language.lower():
                continue
            if model and rec.model_id and model.lower() not in rec.model_id.lower():
                continue
            filtered_ext.append(rec)

        if filtered_ext:
            console.print()
            console.print(render_external_benchmarks_table(filtered_ext))
        elif src_filter == "external":
            console.print("[yellow]No external benchmark reference records matched the specified filters.[/yellow]")


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
