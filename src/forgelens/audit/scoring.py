"""Category scoring engine and final suitability assessment."""

from enum import Enum
from typing import Dict, List, Tuple
from pydantic import BaseModel

from forgelens.audit.profiles import AuditProfile


class FinalStatus(str, Enum):
    SUITABLE = "SUITABLE"
    REVIEW_REQUIRED = "REVIEW_REQUIRED"
    NOT_SUITABLE = "NOT_SUITABLE"
    INSUFFICIENT_DATA = "INSUFFICIENT_DATA"


class ScoreBreakdown(BaseModel):
    category_scores: Dict[str, float]  # Score 0-100 per category
    weighted_total_score: float  # Score 0-100
    final_status: FinalStatus
    status_reasons: List[str]


class ScoringEngine:
    """Calculates category scores and determines final suitability status."""

    @staticmethod
    def calculate_dataset_score(
        category_scores: Dict[str, float],
        profile: AuditProfile,
        total_sampled: int = 0
    ) -> ScoreBreakdown:
        if total_sampled == 0:
            return ScoreBreakdown(
                category_scores=category_scores,
                weighted_total_score=0.0,
                final_status=FinalStatus.INSUFFICIENT_DATA,
                status_reasons=["Insufficient sampled dataset rows available for analysis."],
            )

        weighted_sum = 0.0
        weight_sum = 0.0

        for cat, weight in profile.weights.items():
            score = category_scores.get(cat, 50.0)
            weighted_sum += score * weight
            weight_sum += weight

        total_score = round(weighted_sum / weight_sum if weight_sum > 0 else 50.0, 2)

        reasons: List[str] = []
        for cat, score in category_scores.items():
            if score < 60.0:
                reasons.append(f"Low score in category '{cat}': {score:.1f}/100.")

        if total_score >= 80.0 and not reasons:
            status = FinalStatus.SUITABLE
            reasons.append(f"High overall quality score ({total_score}/100) across all weighted criteria.")
        elif total_score >= 60.0 or len(reasons) <= 2:
            status = FinalStatus.REVIEW_REQUIRED
            if not reasons:
                reasons.append(f"Moderate quality score ({total_score}/100) requires manual review.")
        else:
            status = FinalStatus.NOT_SUITABLE
            reasons.append(f"Low overall quality score ({total_score}/100) failed critical criteria.")

        return ScoreBreakdown(
            category_scores=category_scores,
            weighted_total_score=total_score,
            final_status=status,
            status_reasons=reasons,
        )
