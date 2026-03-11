"""SHA-256 deduplication registry — ensures no payload is sent twice per run."""

from __future__ import annotations

import hashlib


class HashRegistry:
    """Thread-safe SHA-256 payload deduplication registry."""

    def __init__(self) -> None:
        self._seen: set[str] = set()

    def register(self, payload: str) -> bool:
        """
        Register a payload. Returns True if new (not seen before),
        False if duplicate.
        """
        digest = hashlib.sha256(payload.encode()).hexdigest()
        if digest in self._seen:
            return False
        self._seen.add(digest)
        return True

    def is_duplicate(self, payload: str) -> bool:
        digest = hashlib.sha256(payload.encode()).hexdigest()
        return digest in self._seen

    def reset(self) -> None:
        self._seen.clear()

    def __len__(self) -> int:
        return len(self._seen)
