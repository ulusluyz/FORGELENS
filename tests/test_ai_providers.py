"""Unit tests for AI Providers and Budget Controller."""

import pytest
from unittest.mock import patch, MagicMock

from forgelens.providers.budget import AuditBudgetConfig, BudgetTracker
from forgelens.providers.openai_provider import OpenAIProvider, AIProviderError


def test_budget_tracker():
    budget = AuditBudgetConfig(max_samples=100, max_tokens=1000, max_cost_usd=1.00)
    tracker = BudgetTracker()

    assert tracker.can_proceed(budget, estimated_tokens_next=100, estimated_cost_next=0.10) is True

    tracker.record_usage(tokens=950, cost_usd=0.90, samples=50)

    # Token limit check
    assert tracker.can_proceed(budget, estimated_tokens_next=100, estimated_cost_next=0.05) is False

    # Sample limit check
    tracker_samples = BudgetTracker()
    tracker_samples.record_usage(tokens=100, cost_usd=0.10, samples=100)
    assert tracker_samples.can_proceed(budget, estimated_tokens_next=10, estimated_cost_next=0.01) is False


@pytest.mark.asyncio
async def test_openai_provider_validation():
    provider = OpenAIProvider(api_key="sk-mockkey123")

    mock_res = MagicMock()
    mock_res.status_code = 200
    mock_res.json.return_value = {"data": [{"id": "gpt-4o-mini"}, {"id": "gpt-4o"}]}

    with patch("httpx.AsyncClient.get", return_value=mock_res):
        valid = await provider.validate()
        assert valid is True
        models = await provider.get_models()
        assert "gpt-4o-mini" in models


@pytest.mark.asyncio
async def test_openai_provider_analyze_success():
    provider = OpenAIProvider(api_key="sk-mockkey123")

    mock_res = MagicMock()
    mock_res.status_code = 200
    mock_res.json.return_value = {
        "choices": [
            {
                "message": {
                    "content": '{"quality_assessment": "High Quality", "semantic_consistency_score": 92.5, "synthetic_data_indicators": false, "instruction_quality_score": 88.0, "documentation_quality_score": 85.0, "key_findings": ["Well structured"]}'
                }
            }
        ],
        "usage": {"prompt_tokens": 150, "completion_tokens": 50},
    }

    with patch("httpx.AsyncClient.post", return_value=mock_res):
        result = await provider.analyze(
            prompt="Analyze quality", context_data={"sample": "test"}
        )
        assert result.quality_assessment == "High Quality"
        assert result.semantic_consistency_score == 92.5
        assert result.synthetic_data_indicators is False
        assert result.tokens_used == 200


@pytest.mark.asyncio
async def test_openai_provider_budget_exceeded():
    provider = OpenAIProvider(api_key="sk-mockkey123")
    budget = AuditBudgetConfig(max_tokens=100)
    tracker = BudgetTracker()
    tracker.record_usage(tokens=150, cost_usd=0.01, samples=1)

    with pytest.raises(AIProviderError, match="Audit budget limit reached"):
        await provider.analyze(
            prompt="Analyze text", context_data={}, budget=budget, budget_tracker=tracker
        )
