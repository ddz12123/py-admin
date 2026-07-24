"""initial empty baseline

Revision ID: 0001_initial
Revises:
Create Date: 2026-07-24
"""

from collections.abc import Sequence

revision: str = "0001_initial"
down_revision: str | Sequence[str] | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """基础模板不创建任何业务表。"""


def downgrade() -> None:
    """基础模板没有需要回滚的业务表。"""
