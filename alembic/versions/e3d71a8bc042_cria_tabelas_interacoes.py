
"""Cria tabelas para obras ouvidas, escutas, avaliacoes e reviews.

Revision ID: e3d71a8bc042
Revises: 9d7e28b46c1a
"""

from alembic import op
import sqlalchemy as sa


revision = "e3d71a8bc042"
down_revision = "9d7e28b46c1a"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "obras_ouvidas",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("usuario_id", sa.Integer(), nullable=False),
        sa.Column("obra_id", sa.Integer(), nullable=False),
        sa.Column("marcada_em", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["usuario_id"], ["usuarios.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["obra_id"], ["obras.id"], ondelete="CASCADE"
        ),
        sa.UniqueConstraint(
            "usuario_id", "obra_id",
            name="uq_obras_ouvidas_usuario_obra"
        ),
    )

    op.create_table(
        "escutas",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("usuario_id", sa.Integer(), nullable=False),
        sa.Column("obra_id", sa.Integer(), nullable=False),
        sa.Column("ouvida_em", sa.DateTime(timezone=True), nullable=False),
        sa.Column("registrada_em", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["usuario_id"], ["usuarios.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["obra_id"], ["obras.id"], ondelete="CASCADE"
        ),
    )

    op.create_index(
        "ix_escutas_usuario_ouvida_em",
        "escutas",
        ["usuario_id", "ouvida_em"]
    )

    op.create_table(
        "avaliacoes",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("usuario_id", sa.Integer(), nullable=False),
        sa.Column("obra_id", sa.Integer(), nullable=False),
        sa.Column("nota_passos", sa.Integer(), nullable=False),
        sa.Column("criada_em", sa.DateTime(timezone=True), nullable=False),
        sa.Column("atualizada_em", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(
            ["usuario_id"], ["usuarios.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["obra_id"], ["obras.id"], ondelete="CASCADE"
        ),
        sa.UniqueConstraint(
            "usuario_id", "obra_id",
            name="uq_avaliacoes_usuario_obra"
        ),
        sa.CheckConstraint(
            "nota_passos BETWEEN 1 AND 10",
            name="ck_avaliacoes_nota_passos"
        ),
    )

    op.create_table(
        "reviews",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("usuario_id", sa.Integer(), nullable=False),
        sa.Column("obra_id", sa.Integer(), nullable=False),
        sa.Column("texto", sa.Text(), nullable=False),
        sa.Column("criada_em", sa.DateTime(timezone=True), nullable=False),
        sa.Column("atualizada_em", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(
            ["usuario_id"], ["usuarios.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["obra_id"], ["obras.id"], ondelete="CASCADE"
        ),
        sa.UniqueConstraint(
            "usuario_id", "obra_id",
            name="uq_reviews_usuario_obra"
        ),
        sa.CheckConstraint(
            "length(trim(texto)) > 0",
            name="ck_reviews_texto_nao_vazio"
        ),
    )


def downgrade() -> None:
    op.drop_table("reviews")
    op.drop_table("avaliacoes")
    op.drop_index(
        "ix_escutas_usuario_ouvida_em",
        table_name="escutas"
    )
    op.drop_table("escutas")
    op.drop_table("obras_ouvidas")
