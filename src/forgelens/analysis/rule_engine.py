"""Rule Engine for deterministic checks (duplicates, empty ratios, text quality, patterns)."""

import re
from typing import Any, Dict, List
from pydantic import BaseModel

from forgelens.analysis.language import LocalLanguageDetector
from forgelens.analysis.statistics import StatisticsEngine, DatasetStatistics


class RuleCheckResult(BaseModel):
    rule_name: str
    passed: bool
    score_impact: float  # 0 to 100
    details: Dict[str, Any]
    summary: str


class RuleEngineAnalysis(BaseModel):
    total_sampled: int
    language_ratios: Dict[str, float]
    exact_duplicate_count: int
    exact_duplicate_ratio: float
    empty_row_ratio: float
    very_short_text_ratio: float
    very_long_text_ratio: float
    statistics: DatasetStatistics
    checks: List[RuleCheckResult]


class RuleEngine:
    """Executes deterministic rule checks on dataset samples without calling AI API."""

    HTML_PATTERN = re.compile(r"<[^>]+>")
    SPAM_PATTERNS = [re.compile(r"https?://\S+"), re.compile(r"click here", re.IGNORECASE)]

    @classmethod
    def analyze_dataset_sample(
        cls,
        rows: List[Dict[str, Any]],
        text_fields: List[str] = None
    ) -> RuleEngineAnalysis:
        if not rows:
            empty_stats = StatisticsEngine.calculate_dataset_statistics([])
            return RuleEngineAnalysis(
                total_sampled=0,
                language_ratios={},
                exact_duplicate_count=0,
                exact_duplicate_ratio=0.0,
                empty_row_ratio=0.0,
                very_short_text_ratio=0.0,
                very_long_text_ratio=0.0,
                statistics=empty_stats,
                checks=[],
            )

        total_count = len(rows)
        stats = StatisticsEngine.calculate_dataset_statistics(rows)

        # Infer text fields if not provided
        if not text_fields:
            text_fields = [f.name for f in stats.field_stats if f.dtype == "str"]
            if not text_fields and rows:
                text_fields = list(rows[0].keys())

        # Collect concatenated text representation per row
        row_texts: List[str] = []
        for r in rows:
            parts = [str(r[f]) for f in text_fields if f in r and r[f] is not None]
            row_texts.append(" ".join(parts))

        # 1. Exact Duplicate Analysis
        seen_texts = set()
        duplicate_count = 0
        for txt in row_texts:
            norm = txt.strip().lower()
            if norm in seen_texts:
                duplicate_count += 1
            else:
                seen_texts.add(norm)

        dup_ratio = round((duplicate_count / total_count) * 100.0, 2)

        # 2. Empty / Short / Long Text Checks
        empty_count = 0
        short_count = 0
        long_count = 0
        html_count = 0

        for txt in row_texts:
            clean = txt.strip()
            if not clean:
                empty_count += 1
            else:
                if len(clean) < 10:
                    short_count += 1
                elif len(clean) > 10000:
                    long_count += 1

                if cls.HTML_PATTERN.search(clean):
                    html_count += 1

        empty_ratio = round((empty_count / total_count) * 100.0, 2)
        short_ratio = round((short_count / total_count) * 100.0, 2)
        long_ratio = round((long_count / total_count) * 100.0, 2)
        html_ratio = round((html_count / total_count) * 100.0, 2)

        # 3. Local Language Ratios
        lang_ratios = LocalLanguageDetector.analyze_language_distribution(row_texts)

        # 4. Generate Rule Check Results
        checks: List[RuleCheckResult] = []

        # Duplicate Check
        dup_passed = dup_ratio < 15.0
        checks.append(
            RuleCheckResult(
                rule_name="Exact Duplicate Ratio Check",
                passed=dup_passed,
                score_impact=max(0.0, 100.0 - (dup_ratio * 2)),
                details={"exact_duplicate_ratio": dup_ratio, "duplicate_count": duplicate_count},
                summary=f"Exact duplicate ratio is {dup_ratio}% ({duplicate_count}/{total_count}).",
            )
        )

        # Empty Content Check
        empty_passed = empty_ratio < 5.0
        checks.append(
            RuleCheckResult(
                rule_name="Empty Row Ratio Check",
                passed=empty_passed,
                score_impact=max(0.0, 100.0 - (empty_ratio * 5)),
                details={"empty_row_ratio": empty_ratio, "empty_count": empty_count},
                summary=f"Empty row ratio is {empty_ratio}% ({empty_count}/{total_count}).",
            )
        )

        # HTML Artifact Check
        html_passed = html_ratio < 10.0
        checks.append(
            RuleCheckResult(
                rule_name="HTML Artifact Check",
                passed=html_passed,
                score_impact=max(0.0, 100.0 - (html_ratio * 3)),
                details={"html_artifact_ratio": html_ratio, "html_count": html_count},
                summary=f"HTML artifact ratio is {html_ratio}%.",
            )
        )

        return RuleEngineAnalysis(
            total_sampled=total_count,
            language_ratios=lang_ratios,
            exact_duplicate_count=duplicate_count,
            exact_duplicate_ratio=dup_ratio,
            empty_row_ratio=empty_ratio,
            very_short_text_ratio=short_ratio,
            very_long_text_ratio=long_ratio,
            statistics=stats,
            checks=checks,
        )
