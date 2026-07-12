"""sala: parametros (JSON) — dimensiones elásticas de la planta

Las plantas dejan de tener medidas fijas: al crear una sala desde el
asistente, el algoritmo de ajuste calcula sus dimensiones según la colección
y las guarda aquí. Las salas existentes quedan NULL y el 3D usa las medidas
por defecto de su forma (compatibilidad total).

Revision ID: c9d0e1f2a3b4
Revises: b8c9d0e1f2a3
Create Date: 2026-07-12

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "c9d0e1f2a3b4"
down_revision = "b8c9d0e1f2a3"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("sala", schema=None) as batch_op:
        batch_op.add_column(sa.Column("parametros", sa.Text(), nullable=True))


def downgrade():
    with op.batch_alter_table("sala", schema=None) as batch_op:
        batch_op.drop_column("parametros")
