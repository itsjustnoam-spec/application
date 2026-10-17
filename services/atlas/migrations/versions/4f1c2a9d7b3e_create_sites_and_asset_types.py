"""
Creates the sites and asset_types tables.

:author: Noam
:date: 17/10/26
"""
# ----- Imports ----- #

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# ----- Consts ----- #

revision: str = "4f1c2a9d7b3e"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

# ----- Functions ----- #


def upgrade():
    op.create_table(
        "sites",
        sa.Column(
            "id",
            sa.Integer(),
            primary_key=True,
        ),
        sa.Column(
            "name",
            sa.String(length=100),
            nullable=False,
        ),
        sa.Column(
            "address",
            sa.String(length=255),
            nullable=False,
        ),
        sa.Column(
            "timezone",
            sa.String(length=64),
            nullable=False,
        ),
        sa.Column(
            "is_deleted",
            sa.Boolean(),
            nullable=False,
        ),
        sa.UniqueConstraint("name"),
    )
    op.create_table(
        "asset_types",
        sa.Column(
            "id",
            sa.Integer(),
            primary_key=True,
        ),
        sa.Column(
            "name",
            sa.String(length=100),
            nullable=False,
        ),
        sa.Column(
            "category",
            sa.String(length=100),
            nullable=False,
        ),
        sa.Column(
            "inspection_interval_days",
            sa.Integer(),
            nullable=False,
        ),
        sa.Column(
            "is_deleted",
            sa.Boolean(),
            nullable=False,
        ),
        sa.CheckConstraint(
            "inspection_interval_days BETWEEN 1 AND 3650",
            name="ck_asset_types_inspection_interval_days_range",
        ),
        sa.UniqueConstraint("name"),
    )


def downgrade():
    op.drop_table("asset_types")
    op.drop_table("sites")
