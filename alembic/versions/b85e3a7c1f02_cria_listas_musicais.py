
"""Cria as tabelas de listas musicais e seus itens.

Revision ID: b85e3a7c1f02
Revises: a74f1c2e9d06
"""

from alembic import op
import sqlalchemy as sa


revision = "b85e3a7c1f02"
down_revision = "a74f1c2e9d06"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # -----------------------------------------
    # LISTAS MUSICAIS
    # -----------------------------------------

    op.create_table(
        "listas_musicais",

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
            "titulo",
            sa.String(120),
            nullable=False,
        ),

        sa.Column(
            "descricao",
            sa.Text(),
            nullable=True,
        ),

        sa.Column(
            "publica",
            sa.Boolean(),
            nullable=False,
        ),

        sa.Column(
            "criada_em",
            sa.DateTime(timezone=True),
            nullable=False,
        ),

        sa.Column(
            "atualizada_em",
            sa.DateTime(timezone=True),
            nullable=True,
        ),

        sa.ForeignKeyConstraint(
            ["usuario_id"],
            ["usuarios.id"],
            ondelete="CASCADE",
        ),
    )

    # -----------------------------------------
    # ITENS DAS LISTAS
    # -----------------------------------------

    op.create_table(
        "itens_lista",

        sa.Column(
            "id",
            sa.Integer(),
            primary_key=True,
        ),

        sa.Column(
            "lista_id",
            sa.Integer(),
            nullable=False,
        ),

        sa.Column(
            "obra_id",
            sa.Integer(),
            nullable=False,
        ),

        sa.Column(
            "posicao",
            sa.Integer(),
            nullable=False,
        ),

        sa.Column(
            "adicionado_em",
            sa.DateTime(timezone=True),
            nullable=False,
        ),

        sa.ForeignKeyConstraint(
            ["lista_id"],
            ["listas_musicais.id"],
            ondelete="CASCADE",
        ),

        sa.ForeignKeyConstraint(
            ["obra_id"],
            ["obras.id"],
            ondelete="CASCADE",
        ),

        sa.UniqueConstraint(
            "lista_id",
            "obra_id",
            name="uq_itens_lista_obra",
        ),

        sa.CheckConstraint(
            "posicao > 0",
            name="ck_itens_lista_posicao",
        ),
    )


def downgrade() -> None:
    op.drop_table("itens_lista")
    op.drop_table("listas_musicais")
