from uuid import UUID

import httpx
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from backend.app.cover_art import consultar_url_capa
from backend.app.musicbrainz import consultar_obra_por_id
from backend.app.schemas_interacoes import MetadadosObraOficial

router = APIRouter()


class RespostaCapa(BaseModel):
    url: str | None


@router.get(
    "/catalogo/musicbrainz/{id_musicbrainz}",
    response_model=MetadadosObraOficial,
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