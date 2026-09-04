"""Task loader and registry for HarnessBench benchmark tasks."""

import json
from pathlib import Path
from typing import Dict, List, Optional
from harnessbench.models import BenchmarkTask

DEFAULT_TASKS_DIR = Path(__file__).resolve().parent.parent.parent / "tasks"


def load_task_from_dir(task_dir: Path) -> BenchmarkTask:
    """Load a benchmark task specification from a directory."""
    prompt_path = task_dir / "prompt.md"
    golden_patch = task_dir / "golden_solution.patch"
    workspace_dir = task_dir / "workspace"
    meta_path = task_dir / "task.json"

    meta: Dict = {}
    if meta_path.exists():
        try:
            meta = json.loads(meta_path.read_text(encoding="utf-8"))
        except Exception:
            pass

    task_id = meta.get("id", task_dir.name)
    name = meta.get("name", task_dir.name.replace("_", " ").title())
    desc = meta.get("description", "")
    expected_files = meta.get("expected_files", [])

    return BenchmarkTask(
        id=task_id,
        name=name,
        description=desc,
        repository=str(workspace_dir) if workspace_dir.exists() else None,
        prompt_path=prompt_path,
        evaluation_command=["pytest", "test_eval.py"],
        baseline_command=["pytest", "tests/test_baseline.py"],
        golden_patch_path=golden_patch if golden_patch.exists() else None,
        expected_files=expected_files,
    )


def load_all_tasks(tasks_dir: Optional[Path] = None) -> List[BenchmarkTask]:
    """Discover and load all benchmark tasks in the tasks directory."""
    tdir = tasks_dir or DEFAULT_TASKS_DIR
    if not tdir.exists():
        return []

    tasks: List[BenchmarkTask] = []
    for child in sorted(tdir.iterdir()):
        if child.is_dir() and (child / "prompt.md").exists():
            tasks.append(load_task_from_dir(child))
    return tasks


def get_task_by_id(task_id: str, tasks_dir: Optional[Path] = None) -> Optional[BenchmarkTask]:
    """Find a specific task by its ID."""
    all_tasks = load_all_tasks(tasks_dir)
    for t in all_tasks:
        if t.id.lower() == task_id.lower() or t.id.lower().endswith(task_id.lower()):
            return t
    return None
