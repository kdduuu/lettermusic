"""Selecao publica de ate quatro albuns, com substituicao atomica."""
from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from backend.app.catalogo import obter_ou_registrar_obra_oficial
from backend.app.models import FavoritoPerfil, Obra, Usuario


class AlbumFavoritoInvalido(Exception):
    pass


class UsuarioFavoritoInexistente(Exception):
    pass


def dados_album(obra: Obra) -> dict:
    return {
        "id_musicbrainz": obra.id_musicbrainz,
        "titulo": obra.titulo,
        "artista": obra.artista,
    }


def consultar_favoritos_perfil(sessao: Session, usuario_id: int) -> list[dict]:
    obras = sessao.scalars(
        select(Obra)
        .join(FavoritoPerfil, FavoritoPerfil.obra_id == Obra.id)
        .where(FavoritoPerfil.usuario_id == usuario_id)
        .order_by(FavoritoPerfil.posicao)
    ).all()
    return [dados_album(obra) for obra in obras]


def substituir_favoritos_perfil(
    sessao: Session, usuario_id: int, albuns: list[UUID],
) -> list[dict]:
    ids = [str(mbid) for mbid in albuns]
    if len(ids) > 4 or len(set(ids)) != len(ids):
        raise AlbumFavoritoInvalido("Selecao invalida.")

    try:
        # Serializa alteracoes do mesmo dono no PostgreSQL.
        dono = sessao.scalar(
            select(Usuario.id).where(Usuario.id == usuario_id).with_for_update()
        )
        if dono is None:
            raise UsuarioFavoritoInexistente()

        # Metadados oficiais; ordem de resolucao deterministica em concorrencia.
        obras = {}
        for mbid in sorted(ids):
            obra = obter_ou_registrar_obra_oficial(sessao, mbid)
            if (obra.tipo or "").lower() != "album":
                raise AlbumFavoritoInvalido("Selecione apenas albuns.")
            obras[mbid] = obra

        sessao.execute(
            delete(FavoritoPerfil).where(FavoritoPerfil.usuario_id == usuario_id)
        )
        sessao.add_all([
            FavoritoPerfil(usuario_id=usuario_id, posicao=posicao, obra_id=obras[mbid].id)
            for posicao, mbid in enumerate(ids, 1)
        ])
        resultado = [dados_album(obras[mbid]) for mbid in ids]
        sessao.commit()
        return resultado
    except Exception:
        sessao.rollback()
        raise
