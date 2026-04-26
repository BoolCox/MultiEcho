"""add random_prefix_enabled to groups

迁移 ID: c9f5a1b2d3e4
父迁移: 8d4c2a7b91f0
创建时间: 2026-05-06 00:10:00.000000

"""
from __future__ import annotations

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "c9f5a1b2d3e4"
down_revision: str | Sequence[str] | None = "8d4c2a7b91f0"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade(name: str = "") -> None:
    if name:
        return

    op.add_column(
        "groups",
        sa.Column(
            "random_prefix_enabled",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
            comment="是否开启群随机前缀",
        ),
    )


def downgrade(name: str = "") -> None:
    if name:
        return

    op.drop_column("groups", "random_prefix_enabled")

