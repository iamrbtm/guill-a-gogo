from __future__ import annotations

import secrets
import time
import uuid
from dataclasses import dataclass
from typing import Optional


@dataclass
class ChallengeContext:
    challenge: bytes
    user_id: Optional[uuid.UUID] = None
    purpose: str = "registration"
    created_at: float = 0.0


class ChallengeStore:
    """Stores WebAuthn challenges pending verification.

    In-process for development and tests. Swap for a Redis-backed store in
    production (keyed by the challenge id with an expiry).
    """

    def __init__(self, ttl_seconds: int = 300) -> None:
        self._store: dict[str, ChallengeContext] = {}
        self.ttl_seconds = ttl_seconds

    def put(self, user_id: Optional[uuid.UUID], purpose: str, challenge: bytes) -> str:
        cid = secrets.token_urlsafe(16)
        self._store[cid] = ChallengeContext(
            challenge=challenge, user_id=user_id, purpose=purpose, created_at=time.time()
        )
        return cid

    def get(self, cid: str) -> Optional[ChallengeContext]:
        ctx = self._store.get(cid)
        if ctx is None:
            return None
        if time.time() - ctx.created_at > self.ttl_seconds:
            self._store.pop(cid, None)
            return None
        return ctx

    def consume(self, cid: str) -> Optional[ChallengeContext]:
        ctx = self._store.pop(cid, None)
        if ctx is None:
            return None
        if time.time() - ctx.created_at > self.ttl_seconds:
            return None
        return ctx


challenge_store = ChallengeStore()
