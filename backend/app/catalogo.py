from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.models import Obra


def registrar_obra(
    sessao: Session,
    id_musicbrainz: str,
    titulo: str,
    tipo: str | None = None,
    data_lancamento: str | None = None,
    artista: str | None = None
) -> Obra:
    """Insere ou localiza a obra, sem confirmar a transacao."""
    obra = sessao.scalar(
        select(Obra).where(Obra.id_musicbrainz == id_musicbrainz)
    )

    if obra is not None:
        # Completa metadados de obras antigas sem apagar dados existentes.
        if artista and not obra.artista:
            obra.artista = artista
            sessao.flush()
        return obra

    obra = Obra(
        id_musicbrainz=id_musicbrainz,
        titulo=titulo,
        artista=artista,
        tipo=tipo,
        data_lancamento=data_lancamento
    )

    sessao.add(obra)
    sessao.flush()
    return obra


def listar_obras(sessao: Session) -> list[Obra]:
    consulta = select(Obra).order_by(Obra.id).limit(20)
    return list(sessao.scalars(consulta))
