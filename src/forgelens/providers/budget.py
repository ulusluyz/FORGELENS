"""Budget controller to monitor and enforce maximum tokens, cost, and sample limits."""

import logging
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class AuditBudgetConfig(BaseModel):
    max_samples: int = Field(default=1000, description="Maximum dataset rows to sample")
    max_tokens: int = Field(default=100000, description="Maximum total AI API tokens allowed")
    max_cost_usd: float = Field(default=2.00, description="Maximum estimated cost in USD allowed")


class BudgetTracker(BaseModel):
    consumed_tokens: int = 0
    consumed_cost_usd: float = 0.0
    processed_samples: int = 0

    def can_proceed(self, budget: AuditBudgetConfig, estimated_tokens_next: int = 0, estimated_cost_next: float = 0.0) -> bool:
        if self.processed_samples >= budget.max_samples:
            logger.warning(f"Budget limit reached: max_samples ({budget.max_samples}) reached.")
            return False

        if (self.consumed_tokens + estimated_tokens_next) > budget.max_tokens:
            logger.warning(
                f"Budget limit reached: token limit ({budget.max_tokens}) would be exceeded "
                f"({self.consumed_tokens} + {estimated_tokens_next})."
            )
            return False

        if (self.consumed_cost_usd + estimated_cost_next) > budget.max_cost_usd:
            logger.warning(
                f"Budget limit reached: cost limit (${budget.max_cost_usd:.2f}) would be exceeded "
                f"(${self.consumed_cost_usd:.4f} + ${estimated_cost_next:.4f})."
            )
            return False

        return True

    def record_usage(self, tokens: int, cost_usd: float, samples: int = 1):
        self.consumed_tokens += tokens
        self.consumed_cost_usd += round(cost_usd, 6)
        self.processed_samples += samples
