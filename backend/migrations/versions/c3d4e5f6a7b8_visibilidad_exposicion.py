"""exposicion: visibilidad (publica/enlace/codigo) + código de acceso

Añade el control de acceso público/privado por exposición:
- `visibilidad`: publica (portal abierto), enlace (solo con la URL) o
  codigo (pide un código de paso al visitante).
- `codigo_acceso_hash`: hash Werkzeug del código; nunca se guarda en claro.

Las exposiciones existentes quedan como `publica` (comportamiento previo).

Revision ID: c3d4e5f6a7b8
Revises: b2c3d4e5f6a7
Create Date: 2026-07-09

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "c3d4e5f6a7b8"
down_revision = "b2c3d4e5f6a7"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("exposicion", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column(
                "visibilidad",
                sa.String(length=20),
                nullable=False,
                server_default="publica",
            )
        )
        batch_op.add_column(
            sa.Column("codigo_acceso_hash", sa.String(length=255), nullable=True)
        )
        batch_op.create_index("ix_exposicion_visibilidad", ["visibilidad"])


def downgrade():
    with op.batch_alter_table("exposicion", schema=None) as batch_op:
        batch_op.drop_index("ix_exposicion_visibilidad")
        batch_op.drop_column("codigo_acceso_hash")
        batch_op.drop_column("visibilidad")
