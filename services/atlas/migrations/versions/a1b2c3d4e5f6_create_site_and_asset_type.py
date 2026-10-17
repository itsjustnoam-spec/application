"""create site and asset_type tables

Revision ID: a1b2c3d4e5f6
Revises:
Create Date: 2026-10-17 00:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "a1b2c3d4e5f6"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

ASSET_CATEGORY_ENUM = sa.Enum(
    "ELECTRICAL",
    "MECHANICAL",
    "HVAC",
    "SAFETY",
    "OTHER",
    name="assetcategory",
)


def upgrade():
    op.create_table(
        "site",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("address", sa.String(length=500), nullable=False),
        sa.Column("timezone", sa.String(length=64), nullable=False),
        sa.Column("archived", sa.Boolean(), nullable=False),
    )
    op.create_index(
        "uq_site_name_active",
        "site",
        ["name"],
        unique=True,
        postgresql_where=sa.text("archived = false"),
    )
    op.create_table(
        "asset_type",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("category", ASSET_CATEGORY_ENUM, nullable=False),
        sa.Column("inspection_interval_days", sa.Integer(), nullable=False),
        sa.Column("archived", sa.Boolean(), nullable=False),
        sa.CheckConstraint(
            "inspection_interval_days BETWEEN 1 AND 3650",
            name="ck_asset_type_inspection_interval_days_range",
        ),
    )
    op.create_index(
        "uq_asset_type_name_active",
        "asset_type",
        ["name"],
        unique=True,
        postgresql_where=sa.text("archived = false"),
    )


def downgrade():
    op.drop_index("uq_asset_type_name_active", table_name="asset_type")
    op.drop_table("asset_type")
    ASSET_CATEGORY_ENUM.drop(op.get_bind(), checkfirst=True)
    op.drop_index("uq_site_name_active", table_name="site")
    op.drop_table("site")
