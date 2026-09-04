"""Repository pollution and hygiene analyzer."""

from pathlib import Path
from typing import List, Set
from harnessbench.models import PollutionReport


def normalize_rel_path(path_str: str) -> str:
    """Normalize relative path separators to forward slash."""
    return path_str.replace("\\", "/").strip("/").strip()


def analyze_repository_pollution(
    untracked_files: List[str],
    modified_files: List[str],
    expected_files: List[str],
) -> PollutionReport:
    """Analyze repository mutations against expected task files.

    Distinguishes:
    - expected modifications (files in expected_files)
    - unexpected modifications (tracked files modified outside expected_files)
    - untracked artifacts (new scratch files, logs, temp md files, caches)
    """
    normalized_expected: Set[str] = {normalize_rel_path(f) for f in expected_files}

    unexpected_files: List[str] = []
    unexpected_directories: Set[str] = set()
    unrelated_modifications: List[str] = []

    # 1. Check untracked files (e.g., scratchpads, logs, aider cache)
    for u in untracked_files:
        norm_u = normalize_rel_path(u)
        # Skip internal benchmark tracking artifacts if any
        if norm_u.startswith(".task_golden"):
            continue

        unexpected_files.append(norm_u)

        # Detect unexpected directories (e.g. .aider.tags.cache/)
        parts = norm_u.split("/")
        if len(parts) > 1:
            unexpected_directories.add(parts[0])

    # 2. Check modified tracked files
    for m in modified_files:
        norm_m = normalize_rel_path(m)
        if norm_m not in normalized_expected:
            unrelated_modifications.append(norm_m)

    # Calculate pollution score:
    # 1 point per untracked file, 2 points per unrelated modification, 2 points per unexpected dir
    pollution_score = (
        len(unexpected_files)
        + (len(unrelated_modifications) * 2)
        + (len(unexpected_directories) * 2)
    )

    return PollutionReport(
        unexpected_files=sorted(unexpected_files),
        unexpected_directories=sorted(list(unexpected_directories)),
        unrelated_modifications=sorted(unrelated_modifications),
        pollution_score=pollution_score,
    )
