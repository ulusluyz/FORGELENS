"""Size-limited local metadata and sample cache manager."""

import json
import logging
import time
from pathlib import Path
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


class CacheManager:
    """Manages size-capped JSON metadata and sample cache (~/.forgelens/cache)."""

    def __init__(self, cache_dir: Optional[Path] = None, max_size_mb: float = 500.0):
        if cache_dir is None:
            base_dir = Path.home() / ".forgelens" / "cache"
            base_dir.mkdir(parents=True, exist_ok=True)
            self.cache_dir = base_dir
        else:
            self.cache_dir = cache_dir
            self.cache_dir.mkdir(parents=True, exist_ok=True)

        self.max_bytes = int(max_size_mb * 1024 * 1024)

    def _get_key_path(self, key: str) -> Path:
        safe_key = key.replace("/", "_").replace(":", "_")
        return self.cache_dir / f"{safe_key}.json"

    def get(self, key: str, max_age_seconds: Optional[float] = 86400.0) -> Optional[Dict[str, Any]]:
        path = self._get_key_path(key)
        if not path.exists():
            return None

        # Check age if max_age_seconds provided
        if max_age_seconds is not None:
            mtime = path.stat().st_mtime
            if (time.time() - mtime) > max_age_seconds:
                path.unlink(missing_ok=True)
                return None

        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as err:
            logger.debug(f"Failed to load cache key '{key}': {err}")
            return None

    def set(self, key: str, data: Dict[str, Any]):
        path = self._get_key_path(key)
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            self._enforce_size_limit()
        except Exception as err:
            logger.debug(f"Failed to write cache key '{key}': {err}")

    def clear(self):
        for f in self.cache_dir.glob("*.json"):
            try:
                f.unlink()
            except Exception:
                pass

    def get_cache_size_bytes(self) -> int:
        total = 0
        for f in self.cache_dir.glob("*.json"):
            total += f.stat().st_size
        return total

    def _enforce_size_limit(self):
        current_size = self.get_cache_size_bytes()
        if current_size <= self.max_bytes:
            return

        # Sort files by modification time (oldest first)
        files = sorted(self.cache_dir.glob("*.json"), key=lambda p: p.stat().st_mtime)
        for f in files:
            if current_size <= self.max_bytes:
                break
            size = f.stat().st_size
            try:
                f.unlink()
                current_size -= size
            except Exception:
                pass
