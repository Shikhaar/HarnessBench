"""Unit tests for task loading and validation logic."""

from pathlib import Path
from harnessbench.tasks import get_task_by_id, load_all_tasks, validate_task


class TestTaskManager:
    """Test suite for HarnessBench task discovery, loading, and specification schemas."""

    def test_load_all_tasks_discovers_all_languages(self):
        tasks = load_all_tasks()
        assert len(tasks) == 13

        languages = {t.language for t in tasks}
        assert languages == {"python", "typescript", "go", "java", "rust"}

    def test_task_categories_diversity(self):
        tasks = load_all_tasks()
        categories = {t.category for t in tasks}
        assert len(categories) >= 5
        assert "error_handling" in categories
        assert "concurrency" in categories

    def test_get_task_by_id_found_and_not_found(self):
        task = get_task_by_id("rust_error_handling_001")
        assert task is not None
        assert task.language == "rust"
        assert task.category == "error_handling"

        missing = get_task_by_id("non_existent_task_xyz")
        assert missing is None

    def test_validate_representative_python_task(self):
        task = get_task_by_id("python_bugfix_001")
        assert task is not None
        res = validate_task(task)
        assert res.valid is True
        assert res.status == "VALID"
        assert res.baseline_pre_passed is True
        assert res.eval_pre_failed is True
        assert res.golden_patch_applied is True
        assert res.eval_post_passed is True
        assert res.baseline_post_passed is True

    def test_validate_rust_task_environment_classification(self):
        task = get_task_by_id("rust_error_handling_001")
        assert task is not None
        res = validate_task(task)
        # If cargo is not installed, it cleanly classifies as ENVIRONMENT_UNAVAILABLE
        if not res.environment_available:
            assert res.status == "ENVIRONMENT_UNAVAILABLE"
            assert "cargo" in res.errors[0]
        else:
            assert res.valid is True
            assert res.status == "VALID"
