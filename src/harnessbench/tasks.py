"""Task loader, YAML parser, and golden solution validator for HarnessBench."""

import json
import subprocess
from pathlib import Path
from typing import Dict, List, Optional
import yaml

from harnessbench.evaluation.tests import execute_test_command
from harnessbench.execution.sandbox import SandboxWorkspace
from harnessbench.models import BenchmarkTask, TaskValidationResult

DEFAULT_TASKS_DIR = Path(__file__).resolve().parent.parent.parent / "tasks"


def load_task_from_dir(task_dir: Path) -> BenchmarkTask:
    """Load a benchmark task specification from a directory with task.yaml or task.json."""
    prompt_path = task_dir / "prompt.md"
    golden_patch = task_dir / "golden_solution.patch"
    workspace_dir = task_dir / "workspace"
    yaml_path = task_dir / "task.yaml"
    json_path = task_dir / "task.json"

    meta: Dict = {}
    if yaml_path.exists():
        try:
            meta = yaml.safe_load(yaml_path.read_text(encoding="utf-8")) or {}
        except Exception:
            pass
    elif json_path.exists():
        try:
            meta = json.loads(json_path.read_text(encoding="utf-8"))
        except Exception:
            pass

    task_id = meta.get("id", task_dir.name)
    name = meta.get("name", task_dir.name.replace("_", " ").title())
    language = meta.get("language", task_dir.parent.name if task_dir.parent.name in ("python", "typescript", "go", "java") else "python")
    category = meta.get("category", "bug_fixing")
    difficulty = meta.get("difficulty", "medium")
    desc = meta.get("description", "")
    expected_files = meta.get("expected_files", [])
    timeout = meta.get("timeout_seconds", 300)

    # Evaluation command can be a nested dict or string
    eval_section = meta.get("evaluation", {})
    if isinstance(eval_section, dict):
        eval_cmd = eval_section.get("command", "pytest")
    else:
        eval_cmd = meta.get("evaluation_command", "pytest")

    baseline_section = meta.get("baseline", {})
    if isinstance(baseline_section, dict):
        base_cmd = baseline_section.get("command", "pytest")
    else:
        base_cmd = meta.get("baseline_command", "pytest")

    # If repository is specified as relative path in meta
    repo_field = meta.get("repository")
    if isinstance(repo_field, dict):
        repo_path = str(workspace_dir) if workspace_dir.exists() else None
    elif isinstance(repo_field, str):
        custom_repo = task_dir / repo_field
        repo_path = str(custom_repo) if custom_repo.exists() else str(workspace_dir)
    else:
        repo_path = str(workspace_dir) if workspace_dir.exists() else None

    return BenchmarkTask(
        id=task_id,
        name=name,
        language=language,
        category=category,
        difficulty=difficulty,
        description=desc,
        repository=repo_path,
        prompt_path=prompt_path,
        evaluation_command=eval_cmd,
        baseline_command=base_cmd,
        golden_patch_path=golden_patch if golden_patch.exists() else None,
        expected_files=expected_files,
        timeout_seconds=timeout,
    )


def load_all_tasks(tasks_dir: Optional[Path] = None) -> List[BenchmarkTask]:
    """Discover and load all benchmark tasks across language subdirectories and root tasks/."""
    tdir = tasks_dir or DEFAULT_TASKS_DIR
    if not tdir.exists():
        return []

    tasks: List[BenchmarkTask] = []
    # Search directories recursively for task.yaml or prompt.md
    for child in sorted(tdir.rglob("prompt.md")):
        task_dir = child.parent
        tasks.append(load_task_from_dir(task_dir))
    return tasks


def get_task_by_id(task_id: str, tasks_dir: Optional[Path] = None) -> Optional[BenchmarkTask]:
    """Find a specific task by its ID."""
    all_tasks = load_all_tasks(tasks_dir)
    for t in all_tasks:
        if t.id.lower() == task_id.lower() or t.id.lower().endswith(task_id.lower()):
            return t
    return None


def validate_task(task: BenchmarkTask) -> TaskValidationResult:
    """Validate task integrity:

    1. Clean repository -> baseline tests MUST PASS
    2. Clean repository -> evaluation tests MUST FAIL (pre-fix)
    3. Apply golden patch -> MUST APPLY CLEANLY
    4. Evaluation tests -> MUST PASS (post-fix)
    5. Baseline tests -> MUST PASS (no regressions)
    """
    errors: List[str] = []
    template_dir = Path(task.repository) if task.repository else None
    sandbox = SandboxWorkspace(
        task_id=f"val_{task.id}",
        template_dir=template_dir,
        golden_patch_path=task.golden_patch_path,
    )

    baseline_pre_passed = False
    eval_pre_failed = False
    golden_patch_applied = False
    eval_post_passed = False
    baseline_post_passed = False

    with sandbox:
        # Step 1: Baseline tests in clean repo MUST PASS
        base_pass, b_exit_code, b_stdout, b_stderr, _ = execute_test_command(
            command=task.baseline_command,
            cwd=sandbox.path,
        )

        # Detect if command tool is unavailable in environment (e.g. cargo/go/mvn not installed)
        if b_exit_code == 127 or "Command not found" in (b_stderr or "") or "not recognized" in (b_stderr or ""):
            return TaskValidationResult(
                task_id=task.id,
                language=task.language,
                valid=False,
                status="ENVIRONMENT_UNAVAILABLE",
                environment_available=False,
                baseline_pre_passed=False,
                eval_pre_failed=False,
                golden_patch_applied=False,
                eval_post_passed=False,
                baseline_post_passed=False,
                errors=[f"Execution environment missing required runtime for '{task.baseline_command}': {b_stderr.strip()}"],
            )

        baseline_pre_passed = base_pass
        if not base_pass:
            errors.append(f"Baseline tests failed on clean starting state:\n{b_stderr or b_stdout}")

        # Step 2: Evaluation tests in clean repo MUST FAIL
        eval_pass_pre, e_exit_code, e_stdout, e_stderr, _ = execute_test_command(
            command=task.evaluation_command,
            cwd=sandbox.path,
        )
        if e_exit_code == 127 or "Command not found" in (e_stderr or ""):
            return TaskValidationResult(
                task_id=task.id,
                language=task.language,
                valid=False,
                status="ENVIRONMENT_UNAVAILABLE",
                environment_available=False,
                baseline_pre_passed=baseline_pre_passed,
                eval_pre_failed=False,
                golden_patch_applied=False,
                eval_post_passed=False,
                baseline_post_passed=False,
                errors=[f"Execution environment missing required runtime for '{task.evaluation_command}': {e_stderr.strip()}"],
            )

        eval_pre_failed = not eval_pass_pre
        if eval_pass_pre:
            errors.append("Evaluation tests passed on buggy starting state (must fail before fix).")

        # Step 3: Apply golden patch
        if not task.golden_patch_path or not task.golden_patch_path.exists():
            errors.append("No golden_solution.patch found for task.")
        else:
            patch_file = sandbox.path / ".task_golden.patch"
            res = subprocess.run(
                ["git", "apply", "--ignore-whitespace", "--whitespace=nowarn", str(patch_file)],
                cwd=str(sandbox.path),
                capture_output=True,
                text=True,
            )
            golden_patch_applied = (res.returncode == 0)
            if not golden_patch_applied:
                errors.append(f"Golden solution patch failed to apply:\n{res.stderr}")

        # Step 4: Post-fix evaluation tests MUST PASS
        if golden_patch_applied:
            eval_pass_post, _, p_stdout, p_stderr, _ = execute_test_command(
                command=task.evaluation_command,
                cwd=sandbox.path,
            )
            eval_post_passed = eval_pass_post
            if not eval_pass_post:
                errors.append(f"Evaluation tests failed after applying golden patch:\n{p_stderr or p_stdout}")

            # Step 5: Post-fix baseline tests MUST PASS (no regressions)
            base_pass_post, _, bp_stdout, bp_stderr, _ = execute_test_command(
                command=task.baseline_command,
                cwd=sandbox.path,
            )
            baseline_post_passed = base_pass_post
            if not base_pass_post:
                errors.append(f"Baseline tests broke after applying golden patch (regression):\n{bp_stderr or bp_stdout}")

    is_valid = (
        baseline_pre_passed
        and eval_pre_failed
        and golden_patch_applied
        and eval_post_passed
        and baseline_post_passed
    )

    return TaskValidationResult(
        task_id=task.id,
        language=task.language,
        valid=is_valid,
        status="VALID" if is_valid else "INVALID",
        environment_available=True,
        baseline_pre_passed=baseline_pre_passed,
        eval_pre_failed=eval_pre_failed,
        golden_patch_applied=golden_patch_applied,
        eval_post_passed=eval_post_passed,
        baseline_post_passed=baseline_post_passed,
        errors=errors,
    )
