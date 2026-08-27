"""${message}

Revision ID: ${up_revision}
Revises: ${down_revision | comma,n}
Create Date: ${create_date}
"""
from __future__ import annotations

from alembic import op
from app.db.base import Base
from app import models  # noqa: F401  (register models on metadata)
from sqlalchemy.engine import Connection
from sqlalchemy import schema as sa_schema

revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create all Phase 1 tables from the ORM metadata. This is the initial
    # schema; subsequent migrations should use explicit op.create_table calls.
    bind = op.get_bind()
    Base.metadata.create_all(bind=bind)


def downgrade() -> None:
    bind = op.get_bind()
    Base.metadata.drop_all(bind=bind)
