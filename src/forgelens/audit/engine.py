"""Core Audit Engine orchestrating Dataset and Model Audits."""

import logging
from typing import Any, Dict, Optional
from pydantic import BaseModel

from forgelens.connectors.huggingface import HuggingFaceConnector
from forgelens.analysis.rule_engine import RuleEngine
from forgelens.analysis.sampling import SamplingEngine, SamplingStrategy
from forgelens.providers.base import BaseAIProvider
from forgelens.providers.budget import AuditBudgetConfig, BudgetTracker
from forgelens.audit.evidence import EvidenceReport
from forgelens.audit.profiles import BUILTIN_PROFILES, AuditProfile
from forgelens.audit.scoring import ScoreBreakdown, ScoringEngine

logger = logging.getLogger(__name__)


class AuditResult(BaseModel):
    audit_type: str  # "dataset" or "model"
    repo_id: str
    revision: str
    profile_name: str
    ai_enabled: bool
    ai_provider_name: Optional[str] = None
    ai_model_name: Optional[str] = None
    scores: ScoreBreakdown
    evidence: EvidenceReport
    rule_summary: Dict[str, Any]
    ai_summary: Optional[Dict[str, Any]] = None
    warnings: list[str] = []
    errors: list[str] = []


class AuditEngine:
    """Orchestrates dataset and model audits."""

    def __init__(
        self,
        hf_connector: HuggingFaceConnector,
        ai_provider: Optional[BaseAIProvider] = None,
        budget_config: Optional[AuditBudgetConfig] = None,
    ):
        self.hf_connector = hf_connector
        self.ai_provider = ai_provider
        self.budget_config = budget_config or AuditBudgetConfig()
        self.budget_tracker = BudgetTracker()

    async def audit_dataset(
        self,
        repo_id: str,
        profile_name: str = "General Dataset",
        sample_size: int = 1000,
        strategy: SamplingStrategy = SamplingStrategy.RANDOM,
        revision: str = "main",
        ai_model: Optional[str] = None,
    ) -> AuditResult:
        profile = BUILTIN_PROFILES.get(profile_name, BUILTIN_PROFILES["General Dataset"])
        evidence = EvidenceReport()
        warnings: list[str] = []
        errors: list[str] = []

        # 1. Fetch metadata from Hugging Face Connector
        meta = await self.hf_connector.get_dataset_metadata(repo_id, revision=revision)

        evidence.add_evidence(
            claim=f"Dataset metadata fetched for {repo_id}",
            measurement={
                "configs": meta.configs,
                "splits": meta.splits,
                "license": meta.license or "Unknown",
                "row_count": meta.row_count,
            },
            ai_interpretation="Repository structure and metadata available.",
        )

        # 2. Fetch sample dataset rows
        config_name = meta.configs[0] if meta.configs else "default"
        split_name = "train"
        if meta.splits and config_name in meta.splits and meta.splits[config_name]:
            split_name = meta.splits[config_name][0]

        fetch_limit = min(sample_size, self.budget_config.max_samples)
        rows: list[Dict[str, Any]] = []

        try:
            rows = await self.hf_connector.get_dataset_rows(
                repo_id=repo_id, config=config_name, split=split_name, limit=fetch_limit, revision=revision
            )
        except Exception as err:
            warnings.append(f"Failed to fetch dataset rows via Dataset Viewer: {err}")

        # 3. Apply Sampling Strategy if rows fetched
        sampled_rows = SamplingEngine.sample_rows(rows, sample_size=fetch_limit, strategy=strategy)

        # 4. Deterministic Rule Engine Analysis
        rule_analysis = RuleEngine.analyze_dataset_sample(sampled_rows)

        evidence.add_evidence(
            claim="Local Deterministic Rule Analysis",
            measurement={
                "exact_duplicate_ratio": rule_analysis.exact_duplicate_ratio,
                "empty_row_ratio": rule_analysis.empty_row_ratio,
                "language_distribution": rule_analysis.language_ratios,
            },
            evidence_sample=[r for r in sampled_rows[:3]],
            ai_interpretation=f"Exact duplicate ratio: {rule_analysis.exact_duplicate_ratio}%, empty ratio: {rule_analysis.empty_row_ratio}%.",
        )

        # 5. Calculate Deterministic Category Scores
        lang_score = 90.0
        if "Turkish" in profile_name:
            tr_ratio = rule_analysis.language_ratios.get("tr", 0.0)
            lang_score = min(100.0, tr_ratio)

        dup_score = max(0.0, 100.0 - (rule_analysis.exact_duplicate_ratio * 3.0))
        quality_score = max(0.0, 100.0 - (rule_analysis.empty_row_ratio * 5.0) - (rule_analysis.very_short_text_ratio * 2.0))
        structure_score = 90.0 if meta.configs and meta.splits else 60.0
        doc_score = 85.0 if meta.readme_content and len(meta.readme_content) > 100 else 40.0
        safety_score = 90.0

        ai_summary_dict: Optional[Dict[str, Any]] = None

        # 6. Optional AI Analysis
        if self.ai_provider and await self.ai_provider.connect():
            try:
                ai_prompt = (
                    f"Perform semantic quality audit on dataset '{repo_id}'. "
                    f"Profile: {profile_name}. Evaluate semantic consistency, instruction quality, and synthetic data signs."
                )
                ai_context = {
                    "metadata": meta.model_dump(),
                    "language_ratios": rule_analysis.language_ratios,
                    "sample_rows": sampled_rows[:10],
                }

                ai_res = await self.ai_provider.analyze(
                    prompt=ai_prompt,
                    context_data=ai_context,
                    model=ai_model,
                    budget=self.budget_config,
                    budget_tracker=self.budget_tracker,
                )

                ai_summary_dict = ai_res.model_dump()
                quality_score = (quality_score + ai_res.semantic_consistency_score) / 2.0
                doc_score = (doc_score + ai_res.documentation_quality_score) / 2.0

                evidence.add_evidence(
                    claim="AI Qualitative Assessment",
                    measurement={"tokens_used": ai_res.tokens_used, "cost_usd": ai_res.cost_usd},
                    ai_interpretation=ai_res.quality_assessment,
                )
            except Exception as err:
                warnings.append(f"AI Provider evaluation skipped/failed: {err}")

        cat_scores = {
            "language": round(lang_score, 2),
            "quality": round(quality_score, 2),
            "structure": round(structure_score, 2),
            "duplicates": round(dup_score, 2),
            "documentation": round(doc_score, 2),
            "safety": round(safety_score, 2),
        }

        scores = ScoringEngine.calculate_dataset_score(
            category_scores=cat_scores, profile=profile, total_sampled=len(sampled_rows)
        )

        return AuditResult(
            audit_type="dataset",
            repo_id=repo_id,
            revision=revision,
            profile_name=profile_name,
            ai_enabled=self.ai_provider is not None,
            ai_provider_name="OpenAI" if self.ai_provider else None,
            ai_model_name=ai_model if self.ai_provider else None,
            scores=scores,
            evidence=evidence,
            rule_summary=rule_analysis.model_dump(),
            ai_summary=ai_summary_dict,
            warnings=warnings,
            errors=errors,
        )

    async def audit_model(
        self,
        repo_id: str,
        profile_name: str = "General Model Audit",
        revision: str = "main",
        ai_model: Optional[str] = None,
    ) -> AuditResult:
        profile = BUILTIN_PROFILES.get(profile_name, BUILTIN_PROFILES["General Model Audit"])
        evidence = EvidenceReport()
        warnings: list[str] = []
        errors: list[str] = []

        meta = await self.hf_connector.get_model_metadata(repo_id, revision=revision)

        arch_known = meta.architecture is not None
        license_known = meta.license is not None
        readme_known = meta.readme_content is not None and len(meta.readme_content) > 50

        evidence.add_evidence(
            claim="Model Remote Metadata Inspection",
            measurement={
                "architecture": meta.architecture or "Unknown",
                "context_length": meta.context_length or "Not Available",
                "vocab_size": meta.vocab_size or "Not Available",
                "license": meta.license or "Unknown",
            },
            ai_interpretation="Inspected remote config.json, tokenizer_config, and repo tree.",
        )

        arch_score = 90.0 if arch_known else 40.0
        license_score = 100.0 if license_known else 30.0
        doc_score = 85.0 if readme_known else 40.0
        quant_score = 80.0
        finetune_score = 75.0

        ai_summary_dict: Optional[Dict[str, Any]] = None

        if self.ai_provider and await self.ai_provider.connect():
            try:
                ai_prompt = f"Perform model card and metadata audit for model '{repo_id}'."
                ai_context = {"metadata": meta.model_dump()}

                ai_res = await self.ai_provider.analyze(
                    prompt=ai_prompt,
                    context_data=ai_context,
                    model=ai_model,
                    budget=self.budget_config,
                    budget_tracker=self.budget_tracker,
                )

                ai_summary_dict = ai_res.model_dump()
                doc_score = (doc_score + ai_res.documentation_quality_score) / 2.0

                evidence.add_evidence(
                    claim="AI Model Card Assessment",
                    measurement={"tokens_used": ai_res.tokens_used, "cost_usd": ai_res.cost_usd},
                    ai_interpretation=ai_res.quality_assessment,
                )
            except Exception as err:
                warnings.append(f"AI Provider evaluation skipped/failed: {err}")

        cat_scores = {
            "architecture": round(arch_score, 2),
            "license": round(license_score, 2),
            "documentation": round(doc_score, 2),
            "quantization": round(quant_score, 2),
            "fine_tuning": round(finetune_score, 2),
        }

        scores = ScoringEngine.calculate_dataset_score(
            category_scores=cat_scores, profile=profile, total_sampled=1  # Non-zero for model metadata
        )

        return AuditResult(
            audit_type="model",
            repo_id=repo_id,
            revision=revision,
            profile_name=profile_name,
            ai_enabled=self.ai_provider is not None,
            ai_provider_name="OpenAI" if self.ai_provider else None,
            ai_model_name=ai_model if self.ai_provider else None,
            scores=scores,
            evidence=evidence,
            rule_summary={"architecture": meta.architecture, "license": meta.license},
            ai_summary=ai_summary_dict,
            warnings=warnings,
            errors=errors,
        )
