"""Immutable benchmark run history and manifest management."""

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
from harnessbench.models import BenchmarkManifest, BenchmarkReport

DEFAULT_RESULTS_DIR = Path("results")
DEFAULT_HISTORY_DIR = DEFAULT_RESULTS_DIR / "history"


def save_immutable_run_history(
    manifest: BenchmarkManifest,
    report: BenchmarkReport,
    history_dir: Optional[Path] = None,
) -> Path:
    """Save an immutable snapshot of benchmark results, manifest, and summary into history/."""
    hdir = history_dir or DEFAULT_HISTORY_DIR
    # Format directory timestamp cleanly (e.g. 2026-09-04T11-30-00Z)
    ts_str = datetime.utcnow().strftime("%Y-%m-%dT%H-%M-%SZ")
    run_history_dir = hdir / ts_str
    run_history_dir.mkdir(parents=True, exist_ok=True)

    # 1. Save manifest.json
    (run_history_dir / "manifest.json").write_text(
        manifest.model_dump_json(indent=2),
        encoding="utf-8",
    )

    # 2. Save results.json
    (run_history_dir / "results.json").write_text(
        json.dumps([r.model_dump(mode="json") for r in report.runs], indent=2),
        encoding="utf-8",
    )

    # 3. Save leaderboard.json
    (run_history_dir / "leaderboard.json").write_text(
        json.dumps({
            "timestamp": report.timestamp.isoformat(),
            "model": report.model,
            "summary": report.summary,
            "awards": report.awards,
        }, indent=2),
        encoding="utf-8",
    )

    return run_history_dir


def list_benchmark_history(history_dir: Optional[Path] = None) -> List[Dict]:
    """Discover all saved historical benchmark runs."""
    hdir = history_dir or DEFAULT_HISTORY_DIR
    if not hdir.exists():
        return []

    entries = []
    for child in sorted(hdir.iterdir(), reverse=True):
        if child.is_dir() and (child / "manifest.json").exists():
            try:
                manifest_data = json.loads((child / "manifest.json").read_text(encoding="utf-8"))
                leaderboard_data = {}
                if (child / "leaderboard.json").exists():
                    leaderboard_data = json.loads((child / "leaderboard.json").read_text(encoding="utf-8"))
                entries.append({
                    "run_dir": str(child),
                    "timestamp": manifest_data.get("timestamp", child.name),
                    "model": manifest_data.get("model", ""),
                    "repetitions": manifest_data.get("repetitions", 1),
                    "harnesses": list(manifest_data.get("harnesses", {}).keys()),
                    "summary": leaderboard_data.get("summary", {}),
                })
            except Exception:
                pass
    return entries
