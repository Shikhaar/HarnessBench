"""Patch quality and code diff efficiency analyzer."""

from harnessbench.models import PatchQualityMetrics, PollutionReport


def evaluate_patch_quality(
    files_changed: int,
    lines_added: int,
    lines_deleted: int,
    diff_text: str,
    pollution: PollutionReport,
) -> PatchQualityMetrics:
    """Assess patch quality without requiring byte-for-byte similarity with the golden solution.

    Rewards:
    - Minimal churn
    - No unexpected files touched
    - No unrelated modifications
    """
    diff_size = len(diff_text.encode("utf-8"))

    # Base quality score begins at 1.0 (100%)
    score = 1.0

    # Penalize untracked/unexpected files
    score -= len(pollution.unexpected_files) * 0.15

    # Penalize unrelated modifications outside expected_files
    score -= len(pollution.unrelated_modifications) * 0.25

    # Slight penalty for excessive line additions (> 200 lines for a focused fix)
    if lines_added > 200:
        score -= min(0.3, (lines_added - 200) * 0.001)

    # Bound between 0.0 and 1.0
    quality_score = max(0.0, round(score, 3))

    return PatchQualityMetrics(
        files_changed=files_changed,
        lines_added=lines_added,
        lines_deleted=lines_deleted,
        diff_size=diff_size,
        unexpected_files=pollution.unexpected_files,
        unrelated_modifications=pollution.unrelated_modifications,
        quality_score=quality_score,
    )
