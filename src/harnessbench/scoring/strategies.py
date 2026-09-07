"""Scoring strategy architecture for HarnessBench."""

from abc import ABC, abstractmethod
from harnessbench.models import RunResult


class ScoringStrategy(ABC):
    """Abstract base strategy for computing composite scores."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Name of the scoring strategy."""
        pass

    @abstractmethod
    def score(self, result: RunResult) -> float:
        """Compute score for a single task run result."""
        pass


class DefaultBalancedScoringStrategy(ScoringStrategy):
    """Balanced scoring strategy prioritizing correctness, low cost, minimal pollution, and zero regressions."""

    @property
    def name(self) -> str:
        return "balanced_v1"

    def score(self, result: RunResult) -> float:
        if not result.success:
            return 0.0

        score = 100.0
        # Penalize regressions severely
        if result.regression_detected:
            score -= 50.0

        # Penalize repository pollution
        score -= min(20.0, result.pollution_score * 2.0)

        # Reward patch quality
        if result.patch_quality:
            score *= result.patch_quality.quality_score

        return max(0.0, round(score, 2))
