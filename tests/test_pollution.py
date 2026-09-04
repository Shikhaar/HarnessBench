"""Tests for repository pollution detection and hygiene scoring."""

from harnessbench.evaluation.pollution import analyze_repository_pollution


def test_clean_modifications():
    untracked = []
    modified = ["src/rate_limiter.py"]
    expected = ["src/rate_limiter.py"]

    report = analyze_repository_pollution(untracked, modified, expected)
    assert report.pollution_score == 0
    assert len(report.unexpected_files) == 0
    assert len(report.unrelated_modifications) == 0
    assert len(report.unexpected_directories) == 0


def test_untracked_pollution_and_unexpected_files():
    untracked = ["agent_scratch.md", ".aider.tags.cache/tags.db"]
    modified = ["src/rate_limiter.py", "README.md"]
    expected = ["src/rate_limiter.py"]

    report = analyze_repository_pollution(untracked, modified, expected)

    # README.md is an unrelated modification
    assert "README.md" in report.unrelated_modifications
    assert "src/rate_limiter.py" not in report.unrelated_modifications

    # agent_scratch.md is an untracked file
    assert "agent_scratch.md" in report.unexpected_files
    # .aider.tags.cache is an unexpected directory
    assert ".aider.tags.cache" in report.unexpected_directories

    assert report.pollution_score > 0
