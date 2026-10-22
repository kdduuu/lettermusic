
from sqlalchemy import String
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
