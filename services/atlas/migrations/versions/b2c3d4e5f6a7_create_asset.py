"""create asset table

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
Create Date: 2026-10-17 12:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "b2c3d4e5f6a7"
down_revision: str | None = "a1b2c3d4e5f6"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

ASSET_STATUS_ENUM = sa.Enum(
    "OPERATIONAL",
    "NEEDS_ATTENTION",
    "OUT_OF_SERVICE",
    "RETIRED",
    name="assetstatus",
)


def upgrade():
    op.create_table(
        "asset",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("serial_number", sa.String(length=100), nullable=False),
        sa.Column("site_id", sa.Integer(), sa.ForeignKey("site.id"), nullable=False),
        sa.Column("asset_type_id", sa.Integer(), sa.ForeignKey("asset_type.id"), nullable=False),
        sa.Column("status", ASSET_STATUS_ENUM, nullable=False),
        sa.Column("installation_date", sa.Date(), nullable=False),
        sa.Column("notes", sa.String(length=1000), nullable=True),
        sa.Column("archived", sa.Boolean(), nullable=False),
    )
    op.create_index("ix_asset_site_id", "asset", ["site_id"])
    op.create_index("ix_asset_asset_type_id", "asset", ["asset_type_id"])
    op.create_index(
        "uq_asset_serial_number_active",
        "asset",
        ["serial_number"],
        unique=True,
        postgresql_where=sa.text("archived = false"),
    )


def downgrade():
    op.drop_index("uq_asset_serial_number_active", table_name="asset")
    op.drop_index("ix_asset_asset_type_id", table_name="asset")
    op.drop_index("ix_asset_site_id", table_name="asset")
    op.drop_table("asset")
    ASSET_STATUS_ENUM.drop(op.get_bind(), checkfirst=True)
