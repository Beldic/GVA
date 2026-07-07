"""multi-organizador: roles + propiedad (usuario_id en exposicion y autor)

Convierte la plataforma de single-tenant (todo compartido) a multi-organizador:
- usuario: nuevos campos `nombre` y `activo`; roles admin/comisario -> superadmin/organizador.
- exposicion y autor: nueva FK `usuario_id` (dueño), obligatoria.

Backfill seguro para datos existentes (incluida la BD de producción): las
columnas se añaden primero como NULL, se rellenan asignando todos los datos
previos a un organizador legado (creándolo si hiciera falta) y solo entonces se
marcan NOT NULL.

Revision ID: a1b2c3d4e5f6
Revises: 618b523d69f8
Create Date: 2026-07-07

"""
import os
import secrets

import sqlalchemy as sa
from alembic import op
from werkzeug.security import generate_password_hash

# revision identifiers, used by Alembic.
revision = "a1b2c3d4e5f6"
down_revision = "618b523d69f8"
branch_labels = None
depends_on = None


def _backfill(conn) -> None:
    """Remapea roles y asigna dueño a exposiciones y autores huérfanos."""
    # Roles antiguos -> nuevos.
    conn.execute(sa.text("UPDATE usuario SET rol='superadmin' WHERE rol='admin'"))
    conn.execute(sa.text("UPDATE usuario SET rol='organizador' WHERE rol='comisario'"))

    huerfanos_expo = conn.execute(
        sa.text("SELECT COUNT(*) FROM exposicion WHERE usuario_id IS NULL")
    ).scalar()
    huerfanos_autor = conn.execute(
        sa.text("SELECT COUNT(*) FROM autor WHERE usuario_id IS NULL")
    ).scalar()
    if not huerfanos_expo and not huerfanos_autor:
        return  # BD sin datos previos: nada que reasignar.

    # Dueño de los datos legados: el primer organizador existente, o uno nuevo.
    owner_id = conn.execute(
        sa.text("SELECT id FROM usuario WHERE rol='organizador' ORDER BY id LIMIT 1")
    ).scalar()
    if owner_id is None:
        email = os.environ.get("LEGACY_ORG_EMAIL", "afesol@galeria.local")
        pwd = os.environ.get("LEGACY_ORG_PASSWORD") or secrets.token_urlsafe(12)
        conn.execute(
            sa.text(
                "INSERT INTO usuario (email, password_hash, nombre, rol, activo, created_at) "
                "VALUES (:email, :ph, :nombre, 'organizador', :activo, CURRENT_TIMESTAMP)"
            ),
            {
                "email": email,
                "ph": generate_password_hash(pwd),
                "nombre": "AFESOL",
                "activo": True,
            },
        )
        owner_id = conn.execute(
            sa.text("SELECT id FROM usuario WHERE email=:email"), {"email": email}
        ).scalar()
        print(
            f"[migración] Organizador legado creado: '{email}' "
            f"(dueño de los datos existentes). Contraseña temporal: {pwd}"
        )

    conn.execute(
        sa.text("UPDATE exposicion SET usuario_id=:oid WHERE usuario_id IS NULL"),
        {"oid": owner_id},
    )
    conn.execute(
        sa.text("UPDATE autor SET usuario_id=:oid WHERE usuario_id IS NULL"),
        {"oid": owner_id},
    )


def upgrade():
    # 1) usuario: nombre + activo (activo con default para las filas existentes).
    with op.batch_alter_table("usuario", schema=None) as batch_op:
        batch_op.add_column(sa.Column("nombre", sa.String(length=160), nullable=True))
        batch_op.add_column(
            sa.Column(
                "activo",
                sa.Boolean(),
                nullable=False,
                server_default=sa.true(),
            )
        )

    # 2) exposicion y autor: usuario_id como NULL de momento.
    with op.batch_alter_table("exposicion", schema=None) as batch_op:
        batch_op.add_column(sa.Column("usuario_id", sa.Integer(), nullable=True))
    with op.batch_alter_table("autor", schema=None) as batch_op:
        batch_op.add_column(sa.Column("usuario_id", sa.Integer(), nullable=True))

    # 3) Rellenar dueños y roles.
    _backfill(op.get_bind())

    # 4) Marcar NOT NULL + índice + FK, ya sin huérfanos.
    with op.batch_alter_table("exposicion", schema=None) as batch_op:
        batch_op.alter_column(
            "usuario_id", existing_type=sa.Integer(), nullable=False
        )
        batch_op.create_index("ix_exposicion_usuario_id", ["usuario_id"])
        batch_op.create_foreign_key(
            "fk_exposicion_usuario_id", "usuario", ["usuario_id"], ["id"]
        )
    with op.batch_alter_table("autor", schema=None) as batch_op:
        batch_op.alter_column(
            "usuario_id", existing_type=sa.Integer(), nullable=False
        )
        batch_op.create_index("ix_autor_usuario_id", ["usuario_id"])
        batch_op.create_foreign_key(
            "fk_autor_usuario_id", "usuario", ["usuario_id"], ["id"]
        )


def downgrade():
    with op.batch_alter_table("autor", schema=None) as batch_op:
        batch_op.drop_constraint("fk_autor_usuario_id", type_="foreignkey")
        batch_op.drop_index("ix_autor_usuario_id")
        batch_op.drop_column("usuario_id")
    with op.batch_alter_table("exposicion", schema=None) as batch_op:
        batch_op.drop_constraint("fk_exposicion_usuario_id", type_="foreignkey")
        batch_op.drop_index("ix_exposicion_usuario_id")
        batch_op.drop_column("usuario_id")
    with op.batch_alter_table("usuario", schema=None) as batch_op:
        batch_op.drop_column("activo")
        batch_op.drop_column("nombre")

    # Roles de vuelta a los antiguos.
    conn = op.get_bind()
    conn.execute(sa.text("UPDATE usuario SET rol='admin' WHERE rol='superadmin'"))
    conn.execute(sa.text("UPDATE usuario SET rol='comisario' WHERE rol='organizador'"))
