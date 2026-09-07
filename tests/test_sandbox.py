"""Tests for git sandbox lifecycle and snapshotting."""

from pathlib import Path
from harnessbench.execution.sandbox import SandboxWorkspace


def test_sandbox_lifecycle(tmp_path: Path):
    template_dir = tmp_path / "template"
    template_dir.mkdir()
    (template_dir / "src").mkdir()
    (template_dir / "src" / "code.py").write_text("print('hello')", encoding="utf-8")

    sandbox = SandboxWorkspace(task_id="test_task_001", template_dir=template_dir)

    with sandbox:
        assert sandbox.path.exists()
        assert (sandbox.path / "src" / "code.py").exists()

        # Check clean initial status
        initial_status = sandbox.get_status_porcelain()
        assert initial_status.strip() == ""

        # Modify a file
        (sandbox.path / "src" / "code.py").write_text("print('modified')", encoding="utf-8")

        # Create an untracked file
        (sandbox.path / "scratch.txt").write_text("untracked notes", encoding="utf-8")

        diff = sandbox.get_diff()
        assert "+print('modified')" in diff
        assert "-print('hello')" in diff

        files_changed, added, deleted = sandbox.get_diff_stat()
        assert files_changed == 1
        assert added == 1
        assert deleted == 1

        untracked = sandbox.get_untracked_files()
        assert "scratch.txt" in untracked

        modified = sandbox.get_modified_files()
        assert any("code.py" in m for m in modified)

    # Workspace directory should be cleaned up after exit
    assert not sandbox.path.exists()
