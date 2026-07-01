"""add check_results table and monitor last_checked_at

Revision ID: 704dfadbe404
Revises: 814ae5c72e7f
Create Date: 2026-07-01 22:48:11.188098

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '704dfadbe404'
down_revision: Union[str, Sequence[str], None] = '814ae5c72e7f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Добавляет колонку last_checked_at и таблицу check_results."""
    op.add_column("monitors", sa.Column("last_checked_at", sa.DateTime(timezone=True), nullable=True))

    op.create_table(
        "check_results",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column(
            "monitor_id",
            sa.Integer(),
            sa.ForeignKey("monitors.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("status_code", sa.Integer(), nullable=True),
        sa.Column("response_time_ms", sa.Integer(), nullable=True),
        sa.Column("checked_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )


def downgrade() -> None:
    """Удаляет таблицу check_results и колонку last_checked_at."""
    op.drop_table("check_results")
    op.drop_column("monitors", "last_checked_at")
