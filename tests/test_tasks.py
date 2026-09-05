"""Unit tests for task loading and validation logic."""

import pytest
from pathlib import Path
from harnessbench.tasks import load_all_tasks, get_task_by_id, validate_task


class TestTaskManager:
    """Test suite for HarnessBench task discovery, loading, and specification schemas."""

    def test_load_all_tasks_discovers_all_languages(self):
        tasks = load_all_tasks()
        assert len(tasks) == 12

        languages = {t.language for t in tasks}
        assert languages == {"python", "typescript", "go", "java"}

    def test_task_categories_diversity(self):
        tasks = load_all_tasks()
        categories = {t.category for t in tasks}
        assert len(categories) >= 4
        assert "concurrency" in categories or "async" in categories or "bug_fixing" in categories

    def test_get_task_by_id_found_and_not_found(self):
        task = get_task_by_id("python_bugfix_001")
        assert task is not None
        assert task.language == "python"

        missing = get_task_by_id("non_existent_task_xyz")
        assert missing is None

    def test_validate_representative_task(self):
        task = get_task_by_id("python_bugfix_001")
        assert task is not None
        res = validate_task(task)
        assert res.valid is True
        assert res.baseline_pre_passed is True
        assert res.eval_pre_failed is True
        assert res.golden_patch_applied is True
        assert res.eval_post_passed is True
        assert res.baseline_post_passed is True
