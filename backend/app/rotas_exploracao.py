"""Novos contratos de leitura do catalogo."""
from typing import Literal
from uuid import UUID

import httpx
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from backend.app import exploracao as ex
from backend.app.database import obter_sessao
from backend.app.models import Obra

router = APIRouter(prefix="/catalogo/explorar", tags=["Exploracao Musical"])


def consultar(funcao, *args):
    try:
        return funcao(*args)
    except (httpx.HTTPError, ValueError, TypeError, KeyError, AttributeError):
        raise HTTPException(
            status_code=502,
            detail="Catalogo musical temporariamente indisponivel.",
        ) from None


@router.get("/busca", response_model=ex.PaginaExploracao)
def buscar(
    termo: str = Query(min_length=2, max_length=100),
    categoria: ex.Categoria = "albuns",
    pagina: int = Query(default=1, ge=1, le=1000),
    limite: int = Query(default=12, ge=1, le=24),
    artista_id: UUID | None = None,
):
    termo = termo.strip()
    if len(termo) < 2:
        raise HTTPException(422, "Informe pelo menos dois caracteres.")
    if artista_id is not None and categoria == "artistas":
        raise HTTPException(422, "Contexto invalido para busca de artistas.")

    return consultar(
        ex.pesquisar, termo, categoria, pagina, limite,
        str(artista_id) if artista_id else None,
    )


@router.get("/artistas/{mbid}", response_model=ex.ItemExploracao)
def artista(mbid: UUID):
    resultado = consultar(ex.consultar_artista, str(mbid))
    if resultado is None:
        raise HTTPException(404, "Artista nao encontrado.")
    return resultado


@router.get("/artistas/{mbid}/discografia", response_model=ex.PaginaExploracao)
def discografia(
    mbid: UUID,
    pagina: int = Query(default=1, ge=1, le=1000),
    limite: int = Query(default=12, ge=1, le=24),
    tipo: ex.TipoDiscografia = "todos",
):
    return consultar(ex.consultar_discografia, str(mbid), pagina, limite, tipo)


@router.get("/albuns/{mbid}/faixas", response_model=ex.FaixasAlbum)
def faixas(mbid: UUID):
    return consultar(ex.consultar_faixas, str(mbid))


@router.get("/local", response_model=ex.PaginaExploracao)
def catalogo_local(
    termo: str = Query(default="", max_length=100),
    tipo: Literal["todos", "Album", "Single", "EP"] = "todos",
    pagina: int = Query(default=1, ge=1, le=1000),
    limite: int = Query(default=12, ge=1, le=24),
    sessao: Session = Depends(obter_sessao),
):
    consulta = select(Obra)
    termo = termo.strip()

    if termo:
        consulta = consulta.where(or_(
            Obra.titulo.icontains(termo, autoescape=True),
            Obra.artista.icontains(termo, autoescape=True),
        ))

    if tipo != "todos":
        consulta = consulta.where(Obra.tipo == tipo)

    obras = list(sessao.scalars(
        consulta.order_by(Obra.titulo, Obra.id)
        .offset((pagina - 1) * limite)
        .limit(limite + 1)
    ))

    return ex.PaginaExploracao(
        pagina=pagina,
        tem_proxima=len(obras) > limite,
        resultados=[
            ex.ItemExploracao(
                id_musicbrainz=obra.id_musicbrainz,
                titulo=obra.titulo,
                artista=obra.artista,
                tipo=obra.tipo,
                data=obra.data_lancamento,
            )
            for obra in obras[:limite]
        ],
    )
