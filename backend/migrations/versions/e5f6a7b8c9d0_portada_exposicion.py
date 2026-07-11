"""exposicion: obra elegida como portada de la card (portada_obra_id)

Entero sin FK a propósito: una FK exposicion->obra formaría un ciclo con la
cadena obra>zona>sala>exposicion. La propiedad `Exposicion.portada_obra`
valida en lectura que la obra exista y siga colgada en la exposición.

Revision ID: e5f6a7b8c9d0
Revises: d4e5f6a7b8c9
Create Date: 2026-07-11

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "e5f6a7b8c9d0"
down_revision = "d4e5f6a7b8c9"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("exposicion", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column("portada_obra_id", sa.Integer(), nullable=True)
        )


def downgrade():
    with op.batch_alter_table("exposicion", schema=None) as batch_op:
        batch_op.drop_column("portada_obra_id")
