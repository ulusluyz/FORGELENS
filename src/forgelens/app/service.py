"""Unified Application Service Layer for CLI and GUI commands."""

import datetime
import uuid
from typing import Any, Dict, List, Optional

from forgelens.connectors.huggingface import HuggingFaceConnector
from forgelens.providers.openai_provider import OpenAIProvider
from forgelens.providers.budget import AuditBudgetConfig
from forgelens.audit.engine import AuditEngine, AuditResult
from forgelens.analysis.sampling import SamplingStrategy
from forgelens.reports.exporter import ReportExporter
from forgelens.storage.db import StorageManager, AuditHistoryRecord


class ApplicationService:
    """Core Service class managing state and workflows shared by Web GUI & CLI."""

    def __init__(self, db_path: Optional[Any] = None):
        self.db = StorageManager(db_path=db_path)

    def _get_hf_connector(self) -> HuggingFaceConnector:
        hf_prov = self.db.get_provider("huggingface")
        token = hf_prov["api_key"] if hf_prov and hf_prov.get("is_enabled") else None
        return HuggingFaceConnector(token=token)

    def _get_ai_provider(self) -> Optional[OpenAIProvider]:
        ai_prov = self.db.get_provider("openai")
        if ai_prov and ai_prov.get("is_enabled") and ai_prov.get("api_key"):
            return OpenAIProvider(
                api_key=ai_prov["api_key"],
                base_url=ai_prov.get("base_url"),
                default_model=ai_prov.get("default_model"),
            )
        return None

    # --- API Management ---

    def configure_provider(
        self,
        provider_type: str,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        default_model: Optional[str] = None,
        is_enabled: bool = True,
    ):
        self.db.save_provider(
            provider_type=provider_type,
            api_key=api_key,
            base_url=base_url,
            default_model=default_model,
            is_enabled=is_enabled,
        )

    def list_providers(self) -> List[Dict[str, Any]]:
        return self.db.list_providers()

    async def test_provider_connection(self, provider_type: str) -> bool:
        if provider_type == "huggingface":
            connector = self._get_hf_connector()
            return await connector.validate_token()
        elif provider_type == "openai":
            provider = self._get_ai_provider()
            if not provider:
                return False
            return await provider.validate()
        return False

    def remove_provider(self, provider_type: str):
        self.db.delete_provider(provider_type)

    # --- Audit Workflows ---

    async def run_dataset_audit(
        self,
        repo_id: str,
        profile_name: str = "General Dataset",
        sample_size: int = 1000,
        strategy: str = "random",
        revision: str = "main",
        ai_model: Optional[str] = None,
    ) -> AuditResult:
        hf_connector = self._get_hf_connector()
        ai_provider = self._get_ai_provider()

        strat_enum = SamplingStrategy(strategy) if strategy in SamplingStrategy.__members__.values() else SamplingStrategy.RANDOM

        engine = AuditEngine(
            hf_connector=hf_connector,
            ai_provider=ai_provider,
            budget_config=AuditBudgetConfig(max_samples=sample_size),
        )

        result = await engine.audit_dataset(
            repo_id=repo_id,
            profile_name=profile_name,
            sample_size=sample_size,
            strategy=strat_enum,
            revision=revision,
            ai_model=ai_model,
        )

        record = AuditHistoryRecord(
            audit_id=f"audit-{uuid.uuid4().hex[:8]}",
            timestamp=datetime.datetime.now(datetime.timezone.utc).isoformat(),
            audit_type="dataset",
            repo_id=repo_id,
            revision=revision,
            profile_name=profile_name,
            ai_provider="OpenAI" if ai_provider else None,
            ai_model=ai_model,
            final_status=result.scores.final_status.value,
            weighted_total_score=result.scores.weighted_total_score,
            results_json=result.model_dump(),
        )
        self.db.save_audit_record(record)

        return result

    async def run_model_audit(
        self,
        repo_id: str,
        profile_name: str = "General Model Audit",
        revision: str = "main",
        ai_model: Optional[str] = None,
    ) -> AuditResult:
        hf_connector = self._get_hf_connector()
        ai_provider = self._get_ai_provider()

        engine = AuditEngine(
            hf_connector=hf_connector,
            ai_provider=ai_provider,
        )

        result = await engine.audit_model(
            repo_id=repo_id,
            profile_name=profile_name,
            revision=revision,
            ai_model=ai_model,
        )

        record = AuditHistoryRecord(
            audit_id=f"audit-{uuid.uuid4().hex[:8]}",
            timestamp=datetime.datetime.now(datetime.timezone.utc).isoformat(),
            audit_type="model",
            repo_id=repo_id,
            revision=revision,
            profile_name=profile_name,
            ai_provider="OpenAI" if ai_provider else None,
            ai_model=ai_model,
            final_status=result.scores.final_status.value,
            weighted_total_score=result.scores.weighted_total_score,
            results_json=result.model_dump(),
        )
        self.db.save_audit_record(record)

        return result

    # --- Export Workflows ---

    def export_audit_report(self, audit_result: AuditResult, format_type: str = "json") -> str:
        if format_type.lower() == "markdown":
            return ReportExporter.export_markdown(audit_result)
        elif format_type.lower() == "html":
            return ReportExporter.export_html(audit_result)
        return ReportExporter.export_json(audit_result)

    def list_history(self, limit: int = 50) -> List[AuditHistoryRecord]:
        return self.db.list_audit_history(limit=limit)
