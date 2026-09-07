"""Workspace sandbox manager for isolated Git-based execution environments."""

import re
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import List, Optional, Tuple


class SandboxWorkspace:
    """An isolated, disposable Git workspace for running a single harness task."""

    def __init__(self, task_id: str, template_dir: Optional[Path] = None, golden_patch_path: Optional[Path] = None):
        self.task_id = task_id
        self.template_dir = template_dir
        self.golden_patch_path = golden_patch_path
        self._temp_dir: Optional[tempfile.TemporaryDirectory] = None
        self.path: Path = Path()

    def __enter__(self) -> "SandboxWorkspace":
        self._temp_dir = tempfile.TemporaryDirectory(prefix=f"hb_sandbox_{self.task_id}_")
        self.path = Path(self._temp_dir.name).resolve()

        # Copy template files if provided
        if self.template_dir and self.template_dir.exists():
            for item in self.template_dir.iterdir():
                dest = self.path / item.name
                if item.is_dir():
                    shutil.copytree(item, dest, dirs_exist_ok=True)
                else:
                    shutil.copy2(item, dest)

        # Copy golden patch if provided
        if self.golden_patch_path and self.golden_patch_path.exists():
            shutil.copy2(self.golden_patch_path, self.path / ".task_golden.patch")

        # Ensure .gitignore exists for bytecode and testing caches
        gitignore_path = self.path / ".gitignore"
        if not gitignore_path.exists():
            gitignore_path.write_text(
                "__pycache__/\n*.py[cod]\n*$py.class\n.pytest_cache/\n.task_golden.patch\n",
                encoding="utf-8",
            )
        else:
            existing = gitignore_path.read_text(encoding="utf-8")
            if ".task_golden.patch" not in existing:
                gitignore_path.write_text(existing + "\n.task_golden.patch\n", encoding="utf-8")

        # Initialize Git repository
        self._run_git(["init", "-b", "main"])
        self._run_git(["config", "user.name", "HarnessBench Runner"])
        self._run_git(["config", "user.email", "runner@harnessbench.dev"])

        # Stage and commit baseline files
        self._run_git(["add", "-A"])
        # Only commit if there are files staged
        st = self._run_git(["status", "--porcelain"])
        if st.stdout.strip():
            self._run_git(["commit", "-m", "Baseline initial commit"])

        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.cleanup()

    def cleanup(self) -> None:
        """Safely destroy the temporary workspace."""
        if self._temp_dir:
            try:
                self._temp_dir.cleanup()
            except Exception:
                # On Windows, Git can occasionally hold file locks; ignore or retry
                try:
                    shutil.rmtree(self.path, ignore_errors=True)
                except Exception:
                    pass
            self._temp_dir = None

    def _run_git(self, args: List[str]) -> subprocess.CompletedProcess:
        """Run git inside the sandbox workspace."""
        return subprocess.run(
            ["git"] + args,
            cwd=str(self.path),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )

    def get_status_porcelain(self) -> str:
        """Capture git status --porcelain."""
        res = self._run_git(["status", "--porcelain"])
        return res.stdout

    def get_diff(self) -> str:
        """Capture git diff against HEAD."""
        res = self._run_git(["diff", "HEAD"])
        return res.stdout

    def get_diff_stat(self) -> Tuple[int, int, int]:
        """Return (files_changed, lines_added, lines_deleted)."""
        res = self._run_git(["diff", "--shortstat", "HEAD"])
        text = res.stdout.strip()
        if not text:
            return 0, 0, 0

        files_changed = 0
        insertions = 0
        deletions = 0

        # Pattern: 2 files changed, 10 insertions(+), 3 deletions(-)
        m_files = re.search(r"(\d+)\s+file", text)
        m_ins = re.search(r"(\d+)\s+insertion", text)
        m_del = re.search(r"(\d+)\s+deletion", text)

        if m_files:
            files_changed = int(m_files.group(1))
        if m_ins:
            insertions = int(m_ins.group(1))
        if m_del:
            deletions = int(m_del.group(1))

        return files_changed, insertions, deletions

    def get_untracked_files(self) -> List[str]:
        """Return list of untracked files from git status."""
        lines = self.get_status_porcelain().splitlines()
        untracked = []
        for line in lines:
            line = line.strip()
            if line.startswith("??"):
                file_path = line[2:].strip()
                untracked.append(file_path)
        return untracked

    def get_modified_files(self) -> List[str]:
        """Return list of modified or deleted files."""
        lines = self.get_status_porcelain().splitlines()
        modified = []
        for line in lines:
            line = line.strip()
            if not line.startswith("??"):
                parts = line.split(maxsplit=1)
                if len(parts) == 2:
                    modified.append(parts[1].strip())
        return modified
