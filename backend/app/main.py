
import httpx

from fastapi import FastAPI, HTTPException, Query
from backend.app.musicbrainz import pesquisar_obras

app = FastAPI(title="Lettermusic API")


@app.get("/health")
def verificar_saude():
    """Confirma que a API está respondendo."""
    return {"status": "ok"}


@app.get("/catalogo/buscar")
def buscar_obras(
    termo: str = Query(min_length=2, max_length=100),
    artista: str | None = Query(default=None, min_length=2, max_length=100)
):
    try:
        obras = pesquisar_obras(termo, artista)

    except httpx.HTTPError as erro:
        raise HTTPException(
            status_code=502,
            detail="Nao foi possivel consultar o MusicBrainz."
        ) from erro

    return {"resultados": obras}
