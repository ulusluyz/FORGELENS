"""Unit tests for SQLite storage manager and local cache manager."""

import pytest
from pathlib import Path

from forgelens.storage.db import StorageManager, AuditHistoryRecord
from forgelens.storage.cache import CacheManager


def test_storage_manager_providers(tmp_path: Path):
    db_file = tmp_path / "test_forgelens.db"
    db = StorageManager(db_path=db_file)

    # Save provider
    db.save_provider(
        provider_type="openai",
        api_key="sk-secret-key-123",
        base_url="https://api.openai.com/v1",
        default_model="gpt-4o-mini",
        is_enabled=True,
    )

    prov = db.get_provider("openai")
    assert prov is not None
    assert prov["api_key"] == "sk-secret-key-123"
    assert prov["default_model"] == "gpt-4o-mini"
    assert prov["is_enabled"] is True

    providers = db.list_providers()
    assert len(providers) == 1

    # Delete provider
    db.delete_provider("openai")
    assert db.get_provider("openai") is None


def test_storage_manager_audit_history(tmp_path: Path):
    db_file = tmp_path / "test_forgelens.db"
    db = StorageManager(db_path=db_file)

    record = AuditHistoryRecord(
        audit_id="audit-1001",
        timestamp="2025-10-04T12:00:00Z",
        audit_type="dataset",
        repo_id="mock/dataset",
        revision="main",
        profile_name="General Dataset",
        ai_provider="OpenAI",
        ai_model="gpt-4o-mini",
        final_status="SUITABLE",
        weighted_total_score=88.5,
        results_json={"score": 88.5},
    )

    db.save_audit_record(record)

    history = db.list_audit_history()
    assert len(history) == 1
    assert history[0].audit_id == "audit-1001"
    assert history[0].repo_id == "mock/dataset"
    assert history[0].final_status == "SUITABLE"


def test_cache_manager(tmp_path: Path):
    cache_dir = tmp_path / "cache"
    cm = CacheManager(cache_dir=cache_dir, max_size_mb=0.001)  # 1 KB limit

    cm.set("ds_meta_1", {"name": "ds1", "data": "x" * 500})
    data = cm.get("ds_meta_1")
    assert data is not None
    assert data["name"] == "ds1"

    # Push over size limit to trigger eviction
    cm.set("ds_meta_2", {"name": "ds2", "data": "y" * 1000})
    assert cm.get_cache_size_bytes() > 0

    cm.clear()
    assert cm.get_cache_size_bytes() == 0
