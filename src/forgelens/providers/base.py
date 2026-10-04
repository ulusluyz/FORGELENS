"""Base AI Provider interface definition."""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from pydantic import BaseModel

from forgelens.providers.budget import AuditBudgetConfig, BudgetTracker


class AIAnalysisResult(BaseModel):
    provider_name: str
    model_name: str
    quality_assessment: str
    semantic_consistency_score: float  # 0 to 100
    synthetic_data_indicators: bool
    instruction_quality_score: float  # 0 to 100
    documentation_quality_score: float  # 0 to 100
    key_findings: List[str]
    raw_response: Optional[Dict[str, Any]] = None
    tokens_used: int = 0
    cost_usd: float = 0.0


class BaseAIProvider(ABC):
    """Abstract interface for AI evaluation providers."""

    @abstractmethod
    async def connect(self) -> bool:
        pass

    @abstractmethod
    async def validate(self) -> bool:
        pass

    @abstractmethod
    async def get_models(self) -> List[str]:
        pass

    @abstractmethod
    def estimate_cost(self, prompt_tokens: int, completion_tokens: int, model: str) -> float:
        pass

    @abstractmethod
    async def analyze(
        self,
        prompt: str,
        context_data: Dict[str, Any],
        model: Optional[str] = None,
        budget: Optional[AuditBudgetConfig] = None,
        budget_tracker: Optional[BudgetTracker] = None,
    ) -> AIAnalysisResult:
        pass
