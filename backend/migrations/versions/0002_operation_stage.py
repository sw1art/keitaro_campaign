"""operation stage/progress/timestamps

Revision ID: 0002_operation_stage
Revises: 0001_initial
Create Date: 2026-11-17

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0002_operation_stage"
down_revision: Union[str, None] = "0001_initial"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("operations", sa.Column("current_stage", sa.String(length=64), nullable=True))
    op.add_column("operations", sa.Column("progress", sa.Integer(), nullable=False, server_default="0"))
    op.add_column("operations", sa.Column("started_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("operations", sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    op.drop_column("operations", "finished_at")
    op.drop_column("operations", "started_at")
    op.drop_column("operations", "progress")
    op.drop_column("operations", "current_stage")
