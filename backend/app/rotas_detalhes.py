from uuid import UUID

import httpx
from fastapi import APIRouter, HTTPException

from backend.app.musicbrainz import consultar_obra_por_id
from backend.app.schemas_interacoes import MetadadosObraOficial

router = APIRouter()


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