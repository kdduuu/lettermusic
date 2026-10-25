
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.models import Obra


def registrar_obra(
    sessao: Session,
    id_musicbrainz: str,
    titulo: str,
    tipo: str | None = None,
    data_lancamento: str | None = None
) -> Obra:
    # Procura a obra antes de cadastrar.
    obra = sessao.scalar(
        select(Obra).where(Obra.id_musicbrainz == id_musicbrainz)
    )

    if obra is not None:
        return obra

    obra = Obra(
        id_musicbrainz=id_musicbrainz,
        titulo=titulo,
        tipo=tipo,
        data_lancamento=data_lancamento
    )

    sessao.add(obra)
    sessao.commit()
    sessao.refresh(obra)

    return obra
