"""tabla vista_obra: interés anónimo por obra (contemplación 3D / ficha 2D)

Una fila por obra y sesión de navegador, con el modo de la señal:
«3d» = contemplación (mirar el cuadro de cerca unos segundos) y
«2d» = apertura de la ficha en el modo 2D. Sin identidad del visitante.

Revision ID: b8c9d0e1f2a3
Revises: a7b8c9d0e1f2
Create Date: 2026-07-12

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "b8c9d0e1f2a3"
down_revision = "a7b8c9d0e1f2"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "vista_obra",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("obra_id", sa.Integer(), nullable=False),
        sa.Column("modo", sa.String(length=10), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["obra_id"], ["obra.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    with op.batch_alter_table("vista_obra", schema=None) as batch_op:
        batch_op.create_index("ix_vista_obra_obra_id", ["obra_id"])
        batch_op.create_index("ix_vista_obra_created_at", ["created_at"])


def downgrade():
    with op.batch_alter_table("vista_obra", schema=None) as batch_op:
        batch_op.drop_index("ix_vista_obra_created_at")
        batch_op.drop_index("ix_vista_obra_obra_id")
    op.drop_table("vista_obra")
