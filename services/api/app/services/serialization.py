from __future__ import annotations

from sqlalchemy.orm import Session
from sqlalchemy import inspect as sa_inspect

# Fields that are managed by the system, never from client input.
_SYSTEM_FIELDS = {
    "id", "created_at", "updated_at", "deleted_at", "owner_id",
    "user_id", "trip_id", "version", "sequence_version",
}


def column_names(model) -> set[str]:
    return {c.name for c in sa_inspect(model).mapper.columns}


def client_fields(model) -> set[str]:
    return column_names(model) - _SYSTEM_FIELDS


def apply_fields(model, data: dict, *, allowed: set[str] | None = None) -> None:
    fields = allowed if allowed is not None else client_fields(type(model))
    for key, value in data.items():
        if key in fields:
            setattr(model, key, value)


def to_dict(model, *, include: set[str] | None = None, exclude: set[str] | None = None) -> dict:
    cols = column_names(model)
    if include is not None:
        cols = cols & include
    if exclude:
        cols = cols - exclude
    out = {}
    for name in cols:
        val = getattr(model, name)
        if hasattr(val, "isoformat"):
            val = val.isoformat()
        elif isinstance(val, (list, dict)):
            pass
        out[name] = val
    return out
