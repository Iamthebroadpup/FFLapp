from __future__ import annotations
import time
from typing import Any, Optional

class TTLCache:
    def __init__(self, ttl_seconds: int = 600):
        self._ttl = ttl_seconds
        self._data: dict[str, tuple[float, Any]] = {}

    def get(self, key: str) -> Optional[Any]:
        row = self._data.get(key)
        if not row:
            return None
        ts, val = row
        if time.time() - ts > self._ttl:
            self._data.pop(key, None)
            return None
        return val

    def set(self, key: str, value: Any):
        self._data[key] = (time.time(), value)

GLOBAL_CACHE = TTLCache(ttl_seconds=600)
