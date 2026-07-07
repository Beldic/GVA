"""tabla visita: estadísticas de visitas por exposición

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
Create Date: 2026-07-07

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "b2c3d4e5f6a7"
down_revision = "a1b2c3d4e5f6"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "visita",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("exposicion_id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["exposicion_id"], ["exposicion.id"], name="fk_visita_exposicion_id"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    with op.batch_alter_table("visita", schema=None) as batch_op:
        batch_op.create_index("ix_visita_exposicion_id", ["exposicion_id"])
        batch_op.create_index("ix_visita_created_at", ["created_at"])


def downgrade():
    with op.batch_alter_table("visita", schema=None) as batch_op:
        batch_op.drop_index("ix_visita_created_at")
        batch_op.drop_index("ix_visita_exposicion_id")
    op.drop_table("visita")
