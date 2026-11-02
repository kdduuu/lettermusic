
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from backend.app.catalogo import (
    FalhaConsultaMusicBrainz,
    IdentificadorMusicBrainzInvalido,
    ObraNaoEncontradaNoMusicBrainz,
)


def configurar_erros_catalogo(app: FastAPI) -> None:
    """Registra os tratamentos de erros do catalogo musical."""

    @app.exception_handler(IdentificadorMusicBrainzInvalido)
    async def identificador_invalido(
        request: Request,
        erro: IdentificadorMusicBrainzInvalido,
    ) -> JSONResponse:
        return JSONResponse(
            status_code=422,
            content={
                "detail": "ID MusicBrainz invalido.",
            },
        )

    @app.exception_handler(ObraNaoEncontradaNoMusicBrainz)
    async def obra_inexistente(
        request: Request,
        erro: ObraNaoEncontradaNoMusicBrainz,
    ) -> JSONResponse:
        return JSONResponse(
            status_code=404,
            content={
                "detail": "Obra nao encontrada no MusicBrainz.",
            },
        )

    @app.exception_handler(FalhaConsultaMusicBrainz)
    async def falha_musicbrainz(
        request: Request,
        erro: FalhaConsultaMusicBrainz,
    ) -> JSONResponse:
        return JSONResponse(
            status_code=502,
            content={
                "detail": (
                    "Nao foi possivel validar a obra "
                    "no MusicBrainz."
                ),
            },
        )
