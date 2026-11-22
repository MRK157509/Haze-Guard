"""Create the GNSS observations table.

Revision ID: 20261122_0001
Revises:
Create Date: 2026-11-22
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "20261122_0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "gnss_observations",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("node_id", sa.String(), nullable=False),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False),
        sa.Column("signal_type", sa.String(length=16), nullable=False),
        sa.Column("confidence", sa.Numeric(), nullable=False),
        sa.Column("lat", sa.Numeric(), nullable=False),
        sa.Column("lon", sa.Numeric(), nullable=False),
        sa.Column("metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.CheckConstraint("confidence >= 1 AND confidence <= 10", name="ck_gnss_observations_confidence_range"),
        sa.CheckConstraint("signal_type IN ('spoofing', 'jamming')", name="ck_gnss_observations_signal_type"),
        sa.CheckConstraint("lat >= -90 AND lat <= 90", name="ck_gnss_observations_lat_range"),
        sa.CheckConstraint("lon >= -180 AND lon <= 180", name="ck_gnss_observations_lon_range"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_gnss_observations_timestamp", "gnss_observations", ["timestamp"])
    op.create_index("ix_gnss_observations_node_id", "gnss_observations", ["node_id"])
    op.create_index("ix_gnss_observations_signal_type", "gnss_observations", ["signal_type"])


def downgrade() -> None:
    op.drop_index("ix_gnss_observations_signal_type", table_name="gnss_observations")
    op.drop_index("ix_gnss_observations_node_id", table_name="gnss_observations")
    op.drop_index("ix_gnss_observations_timestamp", table_name="gnss_observations")
    op.drop_table("gnss_observations")
