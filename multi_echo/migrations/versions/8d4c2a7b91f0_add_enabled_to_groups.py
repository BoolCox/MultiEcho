"""add enabled to groups

迁移 ID: 8d4c2a7b91f0
父迁移: 439269ca6b0a
创建时间: 2026-05-06 00:00:00.000000

"""
from __future__ import annotations

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "8d4c2a7b91f0"
down_revision: str | Sequence[str] | None = "439269ca6b0a"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade(name: str = "") -> None:
    if name:
        return

    op.add_column(
        "groups",
        sa.Column(
            "enabled",
            sa.Boolean(),
            nullable=False,
            server_default=sa.true(),
            comment="是否启用",
        ),
    )


def downgrade(name: str = "") -> None:
    if name:
        return

    op.drop_column("groups", "enabled")

