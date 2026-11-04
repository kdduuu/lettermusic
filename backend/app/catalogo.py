from uuid import UUID

import httpx

from pydantic import ValidationError
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.models import Obra
from backend.app.musicbrainz import consultar_obra_por_id
from backend.app.persistencia import inserir_se_ausente
from backend.app.schemas_interacoes import MetadadosObraOficial


class IdentificadorMusicBrainzInvalido(Exception):
    """O identificador recebido nao e aceito pelo MusicBrainz."""


class ObraNaoEncontradaNoMusicBrainz(Exception):
    """O identificador nao corresponde a uma obra existente."""


class FalhaConsultaMusicBrainz(Exception):
    """Nao foi possivel obter metadados confiaveis."""


def registrar_obra(
    sessao: Session,
    id_musicbrainz: str,
    titulo: str,
    tipo: str | None = None,
    data_lancamento: str | None = None,
    artista: str | None = None,
) -> Obra:
    """Insere ou localiza a obra, sem confirmar a transacao."""

    obra = sessao.scalar(
        select(Obra).where(Obra.id_musicbrainz == id_musicbrainz)
    )

    if obra is not None:
        # Preserva dados antigos e completa o artista ausente.
        if artista and not obra.artista:
            obra.artista = artista
            sessao.flush()

        return obra

    # O banco resolve a disputa por MBID de forma atomica.
    # Isso preserva o rollback do cadastro quando a operacao principal falha.
    inserir_se_ausente(
        sessao,
        Obra,
        valores={
            "id_musicbrainz": id_musicbrainz,
            "titulo": titulo,
            "artista": artista,
            "tipo": tipo,
            "data_lancamento": data_lancamento,
        },
        colunas_unicas=[Obra.id_musicbrainz],
    )

    return sessao.scalar(
        select(Obra).where(Obra.id_musicbrainz == id_musicbrainz)
    )


def obter_ou_registrar_obra_oficial(
    sessao: Session,
    id_musicbrainz: str,
) -> Obra:
    """Reutiliza uma obra existente ou consulta sua origem oficial."""

    obra = sessao.scalar(
        select(Obra).where(Obra.id_musicbrainz == id_musicbrainz)
    )

    if obra is not None:
        return obra

    try:
        identificador = str(UUID(id_musicbrainz))
    except (ValueError, TypeError, AttributeError) as erro:
        raise IdentificadorMusicBrainzInvalido(
            "ID MusicBrainz invalido."
        ) from erro

    if identificador != id_musicbrainz:
        obra = sessao.scalar(
            select(Obra).where(Obra.id_musicbrainz == identificador)
        )
        if obra is not None:
            return obra

    try:
        dados = consultar_obra_por_id(identificador)
    except httpx.HTTPStatusError as erro:
        if erro.response.status_code == 400:
            try:
                detalhes = erro.response.json()
            except ValueError:
                detalhes = {}

            if (
                isinstance(detalhes, dict)
                and detalhes.get("error") == "Invalid mbid."
            ):
                raise IdentificadorMusicBrainzInvalido(
                    "ID MusicBrainz invalido."
                ) from erro

        raise FalhaConsultaMusicBrainz(
            "Nao foi possivel validar a obra no MusicBrainz."
        ) from erro
    except (httpx.HTTPError, ValueError, TypeError) as erro:
        raise FalhaConsultaMusicBrainz(
            "Nao foi possivel validar a obra no MusicBrainz."
        ) from erro

    if dados is None:
        raise ObraNaoEncontradaNoMusicBrainz(
            "Obra nao encontrada no MusicBrainz."
        )

    try:
        metadados = MetadadosObraOficial.model_validate(dados)
    except ValidationError as erro:
        raise FalhaConsultaMusicBrainz(
            "O MusicBrainz retornou metadados invalidos."
        ) from erro

    return registrar_obra(
        sessao=sessao,
        id_musicbrainz=metadados.id_musicbrainz,
        titulo=metadados.titulo,
        artista=metadados.artista,
        tipo=metadados.tipo,
        data_lancamento=metadados.data_lancamento,
    )


def listar_obras(sessao: Session) -> list[Obra]:
    consulta = select(Obra).order_by(Obra.id).limit(20)
    return list(sessao.scalars(consulta))
