from __future__ import annotations

import hashlib
import hmac
import secrets


def sha256_hex(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def generate_token(length: int = 48) -> str:
    return secrets.token_urlsafe(length)


def generate_recovery_code() -> str:
    # Human-friendly grouping, e.g. XXXX-XXXX-XXXX
    part = lambda: secrets.token_hex(2).upper()
    return "-".join(part() for _ in range(3))


def constant_time_compare(a: str, b: str) -> bool:
    return hmac.compare_digest(a, b)
