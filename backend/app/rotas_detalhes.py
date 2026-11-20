"""Leitura publica e privada de albuns identificados pelo MBID."""
from uuid import UUID

import httpx
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from backend.app.auth import obter_usuario_atual
from backend.app.cover_art import consultar_url_capa
from backend.app.database import obter_sessao
from backend.app.models import (
    Avaliacao, Escuta, Favorito, Obra, ObraOuvida,
    QueroOuvir, Review, Usuario,
)
from backend.app.musicbrainz import consultar_obra_por_id
from backend.app.schemas_interacoes import MetadadosObraOficial
from backend.app.schemas_social import (
    MeuEstadoAlbum, ResumoSocialAlbum, ReviewPublicaResumo,
)

router = APIRouter()


class RespostaCapa(BaseModel):
    url: str | None


@router.get(
    "/catalogo/musicbrainz/{id_musicbrainz}",
    response_model=MetadadosObraOficial,
    response_model_exclude_unset=True,
    tags=["Catálogo Musical"],
)
def detalhar_obra(id_musicbrainz: UUID):
    """Consulta a obra oficial sem gravar dados no banco."""
    try:
        obra = consultar_obra_por_id(str(id_musicbrainz))
    except (httpx.HTTPError, ValueError) as erro:
        raise HTTPException(
            status_code=502,
            detail="Não foi possível consultar o MusicBrainz.",
        ) from erro

    if obra is None:
        raise HTTPException(
            status_code=404,
            detail="Obra não encontrada no MusicBrainz.",
        )

    return obra


@router.get(
    "/catalogo/musicbrainz/{id_musicbrainz}/capa",
    response_model=RespostaCapa,
    tags=["Catálogo Musical"],
)
def consultar_capa(id_musicbrainz: UUID):
    """Consulta a capa sem persistir dados nem bloquear a página do álbum."""
    try:
        url = consultar_url_capa(str(id_musicbrainz))
    except (httpx.HTTPError, ValueError) as erro:
        raise HTTPException(
            status_code=502,
            detail="Não foi possível consultar o Cover Art Archive.",
        ) from erro

    return RespostaCapa(url=url)


@router.get(
    "/catalogo/musicbrainz/{id_musicbrainz}/social",
    response_model=ResumoSocialAlbum,
    tags=["Catálogo Social"],
)
def consultar_social_album(
    id_musicbrainz: UUID,
    sessao: Session = Depends(obter_sessao),
):
    """Retorna dados sociais publicos, sem cadastrar a obra pela visita."""
    obra = sessao.scalar(
        select(Obra).where(Obra.id_musicbrainz == str(id_musicbrainz))
    )
    if obra is None:
        return ResumoSocialAlbum()

    media_passos, quantidade = sessao.execute(
        select(func.avg(Avaliacao.nota_passos), func.count(Avaliacao.id))
        .where(Avaliacao.obra_id == obra.id)
    ).one()

    linhas = sessao.execute(
        select(Review, Usuario)
        .join(Usuario, Usuario.id == Review.usuario_id)
        .where(Review.obra_id == obra.id)
        .order_by(Review.criada_em.desc(), Review.id.desc())
        .limit(6)
    ).all()

    return ResumoSocialAlbum(
        obra_id=obra.id,
        media_avaliacoes=round(float(media_passos) / 2, 2)
        if media_passos is not None else None,
        quantidade_avaliacoes=quantidade,
        reviews=[
            ReviewPublicaResumo(
                username=usuario.username,
                nome_exibicao=usuario.nome_exibicao,
                texto=review.texto,
                criada_em=review.criada_em,
            )
            for review, usuario in linhas
        ],
    )


@router.get(
    "/catalogo/musicbrainz/{id_musicbrainz}/meu-estado",
    response_model=MeuEstadoAlbum,
    tags=["Catálogo Social"],
)
def consultar_meu_estado_album(
    id_musicbrainz: UUID,
    usuario: Usuario = Depends(obter_usuario_atual),
    sessao: Session = Depends(obter_sessao),
):
    """Consulta interacoes do usuario; nao cria obra nem escuta."""
    obra = sessao.scalar(
        select(Obra).where(Obra.id_musicbrainz == str(id_musicbrainz))
    )
    if obra is None:
        return MeuEstadoAlbum()

    def existe(modelo) -> bool:
        return sessao.scalar(
            select(modelo.id).where(
                modelo.usuario_id == usuario.id,
                modelo.obra_id == obra.id,
            ).limit(1)
        ) is not None

    nota_passos = sessao.scalar(
        select(Avaliacao.nota_passos).where(
            Avaliacao.usuario_id == usuario.id,
            Avaliacao.obra_id == obra.id,
        )
    )
    texto_review = sessao.scalar(
        select(Review.texto).where(
            Review.usuario_id == usuario.id,
            Review.obra_id == obra.id,
        )
    )
    escutas = sessao.scalar(
        select(func.count(Escuta.id)).where(
            Escuta.usuario_id == usuario.id,
            Escuta.obra_id == obra.id,
        )
    )

    return MeuEstadoAlbum(
        obra_id=obra.id,
        ouvida=existe(ObraOuvida),
        favorito=existe(Favorito),
        quero_ouvir=existe(QueroOuvir),
        nota=nota_passos / 2 if nota_passos is not None else None,
        review=texto_review,
        quantidade_escutas=escutas or 0,
    )