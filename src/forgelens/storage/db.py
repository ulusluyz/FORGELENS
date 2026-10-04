"""SQLite database storage layer for audit history, providers, and application settings."""

import json
import sqlite3
from pathlib import Path
from typing import Any, Dict, List, Optional
from pydantic import BaseModel


class AuditHistoryRecord(BaseModel):
    id: Optional[int] = None
    audit_id: str
    timestamp: str
    audit_type: str
    repo_id: str
    revision: str
    profile_name: str
    ai_provider: Optional[str] = None
    ai_model: Optional[str] = None
    final_status: str
    weighted_total_score: float
    results_json: Dict[str, Any]


class StorageManager:
    """Manages local SQLite database operations (~/.forgelens/forgelens.db)."""

    def __init__(self, db_path: Optional[Path] = None):
        if db_path is None:
            base_dir = Path.home() / ".forgelens"
            base_dir.mkdir(parents=True, exist_ok=True)
            self.db_path = base_dir / "forgelens.db"
        else:
            self.db_path = db_path
            self.db_path.parent.mkdir(parents=True, exist_ok=True)

        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Audit History Table
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS audit_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    audit_id TEXT UNIQUE NOT NULL,
                    timestamp TEXT NOT NULL,
                    audit_type TEXT NOT NULL,
                    repo_id TEXT NOT NULL,
                    revision TEXT NOT NULL,
                    profile_name TEXT NOT NULL,
                    ai_provider TEXT,
                    ai_model TEXT,
                    final_status TEXT NOT NULL,
                    weighted_total_score REAL NOT NULL,
                    results_json TEXT NOT NULL
                )
            """
            )

            # API Providers / Tokens Table
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS api_providers (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    provider_type TEXT UNIQUE NOT NULL, -- e.g. "openai", "huggingface"
                    api_key TEXT,
                    base_url TEXT,
                    default_model TEXT,
                    is_enabled INTEGER DEFAULT 1
                )
            """
            )

            # Application Settings Table
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS settings (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL
                )
            """
            )
            conn.commit()

    # --- API Providers Management ---

    def save_provider(
        self,
        provider_type: str,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        default_model: Optional[str] = None,
        is_enabled: bool = True,
    ):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO api_providers (provider_type, api_key, base_url, default_model, is_enabled)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(provider_type) DO UPDATE SET
                    api_key = excluded.api_key,
                    base_url = excluded.base_url,
                    default_model = excluded.default_model,
                    is_enabled = excluded.is_enabled
            """,
                (provider_type, api_key, base_url, default_model, 1 if is_enabled else 0),
            )
            conn.commit()

    def get_provider(self, provider_type: str) -> Optional[Dict[str, Any]]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT provider_type, api_key, base_url, default_model, is_enabled FROM api_providers WHERE provider_type = ?",
                (provider_type,),
            )
            row = cursor.fetchone()
            if row:
                return {
                    "provider_type": row["provider_type"],
                    "api_key": row["api_key"],
                    "base_url": row["base_url"],
                    "default_model": row["default_model"],
                    "is_enabled": bool(row["is_enabled"]),
                }
            return None

    def list_providers(self) -> List[Dict[str, Any]]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT provider_type, api_key, base_url, default_model, is_enabled FROM api_providers"
            )
            rows = cursor.fetchall()
            return [
                {
                    "provider_type": r["provider_type"],
                    "api_key": r["api_key"],
                    "base_url": r["base_url"],
                    "default_model": r["default_model"],
                    "is_enabled": bool(r["is_enabled"]),
                }
                for r in rows
            ]

    def delete_provider(self, provider_type: str):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM api_providers WHERE provider_type = ?", (provider_type,))
            conn.commit()

    # --- Audit History Management ---

    def save_audit_record(self, record: AuditHistoryRecord):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO audit_history (
                    audit_id, timestamp, audit_type, repo_id, revision, profile_name,
                    ai_provider, ai_model, final_status, weighted_total_score, results_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    record.audit_id,
                    record.timestamp,
                    record.audit_type,
                    record.repo_id,
                    record.revision,
                    record.profile_name,
                    record.ai_provider,
                    record.ai_model,
                    record.final_status,
                    record.weighted_total_score,
                    json.dumps(record.results_json, ensure_ascii=False),
                ),
            )
            conn.commit()

    def list_audit_history(self, limit: int = 50) -> List[AuditHistoryRecord]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT id, audit_id, timestamp, audit_type, repo_id, revision, profile_name,
                       ai_provider, ai_model, final_status, weighted_total_score, results_json
                FROM audit_history
                ORDER BY id DESC
                LIMIT ?
            """,
                (limit,),
            )
            rows = cursor.fetchall()
            records: List[AuditHistoryRecord] = []
            for r in rows:
                records.append(
                    AuditHistoryRecord(
                        id=r["id"],
                        audit_id=r["audit_id"],
                        timestamp=r["timestamp"],
                        audit_type=r["audit_type"],
                        repo_id=r["repo_id"],
                        revision=r["revision"],
                        profile_name=r["profile_name"],
                        ai_provider=r["ai_provider"],
                        ai_model=r["ai_model"],
                        final_status=r["final_status"],
                        weighted_total_score=r["weighted_total_score"],
                        results_json=json.loads(r["results_json"]),
                    )
                )
            return records
