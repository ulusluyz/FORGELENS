"""OpenAI and OpenAI-Compatible API provider implementation."""

import json
import logging
from typing import Any, Dict, List, Optional
import httpx

from forgelens.providers.base import AIAnalysisResult, BaseAIProvider
from forgelens.providers.budget import AuditBudgetConfig, BudgetTracker

logger = logging.getLogger(__name__)


class AIProviderError(Exception):
    """Custom exception for AI provider errors."""
    pass


class OpenAIProvider(BaseAIProvider):
    """OpenAI and OpenAI-Compatible endpoint client."""

    DEFAULT_BASE_URL = "https://api.openai.com/v1"
    DEFAULT_MODEL = "gpt-4o-mini"

    # Per 1k tokens pricing estimation (Input, Output) in USD
    MODEL_PRICING = {
        "gpt-4o": (0.0025, 0.0100),
        "gpt-4o-mini": (0.00015, 0.00060),
        "gpt-4-turbo": (0.0100, 0.0300),
        "gpt-3.5-turbo": (0.0005, 0.0015),
    }

    def __init__(
        self,
        api_key: str,
        base_url: Optional[str] = None,
        default_model: Optional[str] = None,
        timeout: float = 30.0,
    ):
        self.api_key = api_key.strip() if api_key else ""
        self.base_url = (base_url or self.DEFAULT_BASE_URL).rstrip("/")
        self.default_model = default_model or self.DEFAULT_MODEL
        self.timeout = timeout

    def _get_headers(self) -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "User-Agent": "ForgeLens-Auditor/0.1.0",
        }

    async def connect(self) -> bool:
        return bool(self.api_key)

    async def validate(self) -> bool:
        if not self.api_key:
            return False
        try:
            models = await self.get_models()
            return len(models) > 0
        except Exception:
            return False

    async def get_models(self) -> List[str]:
        if not self.api_key:
            return [self.default_model]

        url = f"{self.base_url}/models"
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                res = await client.get(url, headers=self._get_headers())
                if res.status_code == 200:
                    data = res.json()
                    model_list = [m["id"] for m in data.get("data", []) if "id" in m]
                    return model_list if model_list else [self.default_model]
            except Exception as err:
                logger.debug(f"Failed to fetch models list from {url}: {err}")

        return [self.default_model, "gpt-4o", "gpt-4o-mini"]

    def estimate_cost(self, prompt_tokens: int, completion_tokens: int, model: str) -> float:
        pricing = self.MODEL_PRICING.get(model, (0.001, 0.002))
        input_cost = (prompt_tokens / 1000.0) * pricing[0]
        output_cost = (completion_tokens / 1000.0) * pricing[1]
        return round(input_cost + output_cost, 6)

    async def analyze(
        self,
        prompt: str,
        context_data: Dict[str, Any],
        model: Optional[str] = None,
        budget: Optional[AuditBudgetConfig] = None,
        budget_tracker: Optional[BudgetTracker] = None,
    ) -> AIAnalysisResult:
        selected_model = model or self.default_model

        # Rough token estimation before call (~1 token per 4 chars)
        estimated_prompt_tokens = len(prompt) // 4
        estimated_cost = self.estimate_cost(estimated_prompt_tokens, 500, selected_model)

        if budget and budget_tracker:
            if not budget_tracker.can_proceed(budget, estimated_prompt_tokens, estimated_cost):
                raise AIProviderError("Audit budget limit reached! AI Analysis halted.")

        system_instruction = (
            "You are ForgeLens, an objective AI dataset and model auditor. "
            "Analyze the provided metadata and sample records. "
            "Return strictly JSON formatted output matching this schema:\n"
            "{\n"
            '  "quality_assessment": "Short narrative assessment",\n'
            '  "semantic_consistency_score": 0.0 to 100.0,\n'
            '  "synthetic_data_indicators": true/false,\n'
            '  "instruction_quality_score": 0.0 to 100.0,\n'
            '  "documentation_quality_score": 0.0 to 100.0,\n'
            '  "key_findings": ["Finding 1", "Finding 2"]\n'
            "}"
        )

        user_content = f"{prompt}\n\nContext Data:\n{json.dumps(context_data, ensure_ascii=False)}"

        payload = {
            "model": selected_model,
            "messages": [
                {"role": "system", "content": system_instruction},
                {"role": "user", "content": user_content},
            ],
            "response_format": {"type": "json_object"},
            "temperature": 0.2,
        }

        url = f"{self.base_url}/chat/completions"
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                res = await client.post(url, headers=self._get_headers(), json=payload)
                if res.status_code == 401:
                    raise AIProviderError("Invalid API Key (401 Unauthorized).")
                if res.status_code == 429:
                    raise AIProviderError("Rate limit exceeded (429).")
                res.raise_for_status()

                res_json = res.json()
                usage = res_json.get("usage", {})
                p_tokens = usage.get("prompt_tokens", estimated_prompt_tokens)
                c_tokens = usage.get("completion_tokens", 300)
                total_tokens = p_tokens + c_tokens

                actual_cost = self.estimate_cost(p_tokens, c_tokens, selected_model)

                if budget_tracker:
                    budget_tracker.record_usage(total_tokens, actual_cost, samples=0)

                choice_content = res_json["choices"][0]["message"]["content"]
                parsed_data = json.loads(choice_content)

                return AIAnalysisResult(
                    provider_name="OpenAI",
                    model_name=selected_model,
                    quality_assessment=parsed_data.get("quality_assessment", "N/A"),
                    semantic_consistency_score=float(parsed_data.get("semantic_consistency_score", 70.0)),
                    synthetic_data_indicators=bool(parsed_data.get("synthetic_data_indicators", False)),
                    instruction_quality_score=float(parsed_data.get("instruction_quality_score", 70.0)),
                    documentation_quality_score=float(parsed_data.get("documentation_quality_score", 70.0)),
                    key_findings=parsed_data.get("key_findings", []),
                    raw_response=res_json,
                    tokens_used=total_tokens,
                    cost_usd=actual_cost,
                )
            except json.JSONDecodeError as err:
                raise AIProviderError(f"Malformed JSON response from AI Provider: {err}")
            except httpx.HTTPError as err:
                raise AIProviderError(f"HTTP Error during AI Provider request: {err}")
