
from datetime import datetime, timezone

from sqlalchemy import DateTime, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class Obra(Base):
    __tablename__ = "obras"

    id: Mapped[int] = mapped_column(primary_key=True)
    id_musicbrainz: Mapped[str] = mapped_column(
        String(36), unique=True
    )
    titulo: Mapped[str] = mapped_column(String(255))
    tipo: Mapped[str | None] = mapped_column(String(30))
    data_lancamento: Mapped[str | None] = mapped_column(String(10))


class Usuario(Base):
    __tablename__ = "usuarios"

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(
        String(30), unique=True
    )
    nome_exibicao: Mapped[str] = mapped_column(String(80))
    email: Mapped[str] = mapped_column(
        String(254), unique=True
    )
    senha_hash: Mapped[str] = mapped_column(String(255))
    bio: Mapped[str | None] = mapped_column(String(300))
    criado_em: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc)
    )
