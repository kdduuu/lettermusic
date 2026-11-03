
from uuid import UUID

import httpx

from pydantic import ValidationError
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.models import Obra
from backend.app.musicbrainz import consultar_obra_por_id
from backend.app.schemas_interacoes import ObraInteracao


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
        select(Obra).where(
            Obra.id_musicbrainz == id_musicbrainz
        )
    )

    if obra is not None:
        # Preserva dados antigos e completa o artista ausente.
        if artista and not obra.artista:
            obra.artista = artista
            sessao.flush()

        return obra

    obra = Obra(
        id_musicbrainz=id_musicbrainz,
        titulo=titulo,
        artista=artista,
        tipo=tipo,
        data_lancamento=data_lancamento,
    )

    sessao.add(obra)
    sessao.flush()

    return obra


def obter_ou_registrar_obra_oficial(
    sessao: Session,
    id_musicbrainz: str,
) -> Obra:
    """Reutiliza uma obra existente ou consulta sua origem oficial."""

    # Primeiro consulta o banco, sem depender da internet.
    obra = sessao.scalar(
        select(Obra).where(
            Obra.id_musicbrainz == id_musicbrainz
        )
    )

    if obra is not None:
        return obra

    # Valida e normaliza o identificador recebido.
    try:
        identificador = str(UUID(id_musicbrainz))
    except (ValueError, TypeError, AttributeError) as erro:
        raise IdentificadorMusicBrainzInvalido(
            "ID MusicBrainz invalido."
        ) from erro

    # Evita cadastrar novamente um ID ja normalizado.
    if identificador != id_musicbrainz:
        obra = sessao.scalar(
            select(Obra).where(
                Obra.id_musicbrainz == identificador
            )
        )

        if obra is not None:
            return obra

    # A obra ainda nao existe localmente: consulta o MusicBrainz.
    try:
        dados = consultar_obra_por_id(identificador)

    except httpx.HTTPStatusError as erro:
        # Diferencia um MBID rejeitado de uma falha do servico.
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

    # Confere os tipos e tamanhos antes de salvar no banco.
    try:
        metadados = ObraInteracao.model_validate(dados)
    except ValidationError as erro:
        raise FalhaConsultaMusicBrainz(
            "O MusicBrainz retornou metadados invalidos."
        ) from erro

    # Somente dados oficiais sao utilizados no novo cadastro.
    return registrar_obra(
        sessao=sessao,
        id_musicbrainz=metadados.id_musicbrainz,
        titulo=metadados.titulo,
        artista=metadados.artista,
        tipo=metadados.tipo,
        data_lancamento=metadados.data_lancamento,
    )


def listar_obras(sessao: Session) -> list[Obra]:
    consulta = (
        select(Obra)
        .order_by(Obra.id)
        .limit(20)
    )

    return list(sessao.scalars(consulta))
