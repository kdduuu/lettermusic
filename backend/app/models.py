
from datetime import datetime, timezone

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


def agora_utc() -> datetime:
    return datetime.now(timezone.utc)


class Base(DeclarativeBase):
    pass


class Obra(Base):
    __tablename__ = "obras"

    id: Mapped[int] = mapped_column(primary_key=True)
    id_musicbrainz: Mapped[str] = mapped_column(String(36), unique=True)
    titulo: Mapped[str] = mapped_column(String(255))
    artista: Mapped[str | None] = mapped_column(String(255))
    tipo: Mapped[str | None] = mapped_column(String(30))
    data_lancamento: Mapped[str | None] = mapped_column(String(10))


class Usuario(Base):
    __tablename__ = "usuarios"

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(30), unique=True)
    nome_exibicao: Mapped[str] = mapped_column(String(80))
    email: Mapped[str] = mapped_column(String(254), unique=True)
    senha_hash: Mapped[str] = mapped_column(String(255))
    bio: Mapped[str | None] = mapped_column(String(300))
    criado_em: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=agora_utc
    )


class ObraOuvida(Base):
    """Marca 'Ja ouvi' sem exigir uma escuta com data."""

    __tablename__ = "obras_ouvidas"
    __table_args__ = (
        UniqueConstraint(
            "usuario_id", "obra_id", name="uq_obras_ouvidas_usuario_obra"
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    usuario_id: Mapped[int] = mapped_column(
        ForeignKey("usuarios.id", ondelete="CASCADE")
    )
    obra_id: Mapped[int] = mapped_column(
        ForeignKey("obras.id", ondelete="CASCADE")
    )
    marcada_em: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=agora_utc
    )


class Escuta(Base):
    """Historico: permite varias escutas da mesma obra pelo usuario."""

    __tablename__ = "escutas"
    __table_args__ = (
        Index("ix_escutas_usuario_ouvida_em", "usuario_id", "ouvida_em"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    usuario_id: Mapped[int] = mapped_column(
        ForeignKey("usuarios.id", ondelete="CASCADE")
    )
    obra_id: Mapped[int] = mapped_column(
        ForeignKey("obras.id", ondelete="CASCADE")
    )
    ouvida_em: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=agora_utc
    )
    registrada_em: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=agora_utc
    )


class Avaliacao(Base):
    """Uma nota atual por usuario/obra; 1..10 equivale a 0,5..5."""

    __tablename__ = "avaliacoes"
    __table_args__ = (
        UniqueConstraint(
            "usuario_id", "obra_id", name="uq_avaliacoes_usuario_obra"
        ),
        CheckConstraint(
            "nota_passos BETWEEN 1 AND 10", name="ck_avaliacoes_nota_passos"
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    usuario_id: Mapped[int] = mapped_column(
        ForeignKey("usuarios.id", ondelete="CASCADE")
    )
    obra_id: Mapped[int] = mapped_column(
        ForeignKey("obras.id", ondelete="CASCADE")
    )
    nota_passos: Mapped[int]
    criada_em: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=agora_utc
    )
    atualizada_em: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True)
    )


class Review(Base):
    """Uma review atual por usuario/obra, editavel pelo autor."""

    __tablename__ = "reviews"
    __table_args__ = (
        UniqueConstraint(
            "usuario_id", "obra_id", name="uq_reviews_usuario_obra"
        ),
        CheckConstraint(
            "length(trim(texto)) > 0", name="ck_reviews_texto_nao_vazio"
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    usuario_id: Mapped[int] = mapped_column(
        ForeignKey("usuarios.id", ondelete="CASCADE")
    )
    obra_id: Mapped[int] = mapped_column(
        ForeignKey("obras.id", ondelete="CASCADE")
    )
    texto: Mapped[str] = mapped_column(Text)
    criada_em: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=agora_utc
    )
    atualizada_em: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True)
    )
