"""Unit tests for Evidence, Profiles, Scoring, and Audit Engine."""

import pytest
from unittest.mock import patch, MagicMock

from forgelens.connectors.huggingface import HuggingFaceConnector, DatasetMeta, ModelMeta
from forgelens.audit.evidence import EvidenceReport
from forgelens.audit.profiles import BUILTIN_PROFILES
from forgelens.audit.scoring import ScoringEngine, FinalStatus
from forgelens.audit.engine import AuditEngine


def test_evidence_report():
    report = EvidenceReport()
    report.add_evidence(
        claim="Language distribution",
        measurement={"tr": 93.4, "en": 6.6},
        ai_interpretation="High Turkish concentration.",
    )
    assert len(report.items) == 1
    assert report.items[0].measurement["tr"] == 93.4


def test_scoring_engine():
    profile = BUILTIN_PROFILES["General Dataset"]
    cat_scores = {
        "language": 90.0,
        "quality": 85.0,
        "structure": 95.0,
        "duplicates": 80.0,
        "documentation": 75.0,
        "safety": 90.0,
    }
    score_breakdown = ScoringEngine.calculate_dataset_score(
        category_scores=cat_scores, profile=profile, total_sampled=100
    )
    assert score_breakdown.weighted_total_score > 80.0
    assert score_breakdown.final_status == FinalStatus.SUITABLE


@pytest.mark.asyncio
async def test_audit_engine_dataset_deterministic():
    mock_connector = MagicMock(spec=HuggingFaceConnector)

    mock_connector.get_dataset_metadata.return_value = DatasetMeta(
        repo_id="mock/ds",
        configs=["default"],
        splits={"default": ["train"]},
        license="mit",
        readme_content="# README",
    )
    mock_connector.get_dataset_rows.return_value = [
        {"text": "Sample row 1"},
        {"text": "Sample row 2"},
    ]

    engine = AuditEngine(hf_connector=mock_connector, ai_provider=None)
    result = await engine.audit_dataset("mock/ds")

    assert result.audit_type == "dataset"
    assert result.ai_enabled is False
    assert result.scores.final_status in [FinalStatus.SUITABLE, FinalStatus.REVIEW_REQUIRED]
    assert len(result.evidence.items) >= 2


@pytest.mark.asyncio
async def test_audit_engine_model_deterministic():
    mock_connector = MagicMock(spec=HuggingFaceConnector)

    mock_connector.get_model_metadata.return_value = ModelMeta(
        repo_id="mock/model",
        architecture="LlamaForCausalLM",
        license="apache-2.0",
        readme_content="# Model Card",
    )

    engine = AuditEngine(hf_connector=mock_connector, ai_provider=None)
    result = await engine.audit_model("mock/model")

    assert result.audit_type == "model"
    assert result.scores.category_scores["architecture"] == 90.0
    assert result.scores.category_scores["license"] == 100.0
