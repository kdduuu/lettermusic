
"""Cria as tabelas de favoritos e quero ouvir.

Revision ID: a74f1c2e9d06
Revises: e3d71a8bc042
"""

from alembic import op
import sqlalchemy as sa


revision = "a74f1c2e9d06"
down_revision = "e3d71a8bc042"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Tabela de favoritos
    op.create_table(
        "favoritos",
        sa.Column(
            "id",
            sa.Integer(),
            primary_key=True,
        ),
        sa.Column(
            "usuario_id",
            sa.Integer(),
            nullable=False,
        ),
        sa.Column(
            "obra_id",
            sa.Integer(),
            nullable=False,
        ),
        sa.Column(
            "adicionado_em",
            sa.DateTime(timezone=True),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["usuario_id"],
            ["usuarios.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["obra_id"],
            ["obras.id"],
            ondelete="CASCADE",
        ),
        sa.UniqueConstraint(
            "usuario_id",
            "obra_id",
            name="uq_favoritos_usuario_obra",
        ),
    )

    # Tabela de obras para ouvir futuramente
    op.create_table(
        "quero_ouvir",
        sa.Column(
            "id",
            sa.Integer(),
            primary_key=True,
        ),
        sa.Column(
            "usuario_id",
            sa.Integer(),
            nullable=False,
        ),
        sa.Column(
            "obra_id",
            sa.Integer(),
            nullable=False,
        ),
        sa.Column(
            "adicionado_em",
            sa.DateTime(timezone=True),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["usuario_id"],
            ["usuarios.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["obra_id"],
            ["obras.id"],
            ondelete="CASCADE",
        ),
        sa.UniqueConstraint(
            "usuario_id",
            "obra_id",
            name="uq_quero_ouvir_usuario_obra",
        ),
    )


def downgrade() -> None:
    op.drop_table("quero_ouvir")
    op.drop_table("favoritos")
