
from unittest.mock import patch

import httpx
import pytest

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from backend.app.catalogo import (
    FalhaConsultaMusicBrainz,
    IdentificadorMusicBrainzInvalido,
    ObraNaoEncontradaNoMusicBrainz,
    obter_ou_registrar_obra_oficial,
)
from backend.app.models import Base, Obra


MBID_TESTE = "b1392450-e666-3926-a536-22c65f834433"

DADOS_OFICIAIS = {
    "id_musicbrainz": MBID_TESTE,
    "titulo": "OK Computer",
    "artista": "Radiohead",
    "tipo": "Album",
    "data_lancamento": "1997-05-21",
}


# -----------------------------------------
# BANCO TEMPORARIO
# -----------------------------------------


@pytest.fixture
def sessao():
    """Cria um banco SQLite isolado para cada teste."""

    motor = create_engine("sqlite+pysqlite:///:memory:")

    Base.metadata.create_all(motor)

    try:
        with Session(motor) as sessao_teste:
            yield sessao_teste
    finally:
        motor.dispose()


# -----------------------------------------
# OBRA JA EXISTENTE
# -----------------------------------------


def test_reutiliza_obra_sem_consultar_musicbrainz(sessao):
    obra_original = Obra(
        id_musicbrainz=MBID_TESTE,
        titulo="Titulo preservado",
        artista="Artista preservado",
        tipo="Album",
    )

    sessao.add(obra_original)
    sessao.commit()

    with patch(
        "backend.app.catalogo.consultar_obra_por_id"
    ) as consulta:
        obra = obter_ou_registrar_obra_oficial(
            sessao,
            MBID_TESTE,
        )

    consulta.assert_not_called()

    assert obra.id == obra_original.id
    assert obra.titulo == "Titulo preservado"
    assert obra.artista == "Artista preservado"


def test_reconhece_id_existente_em_maiusculas(sessao):
    sessao.add(
        Obra(
            id_musicbrainz=MBID_TESTE,
            titulo="OK Computer",
            artista="Radiohead",
        )
    )
    sessao.commit()

    with patch(
        "backend.app.catalogo.consultar_obra_por_id"
    ) as consulta:
        obra = obter_ou_registrar_obra_oficial(
            sessao,
            MBID_TESTE.upper(),
        )

    assert obra.id_musicbrainz == MBID_TESTE
    consulta.assert_not_called()


# -----------------------------------------
# CADASTRO OFICIAL
# -----------------------------------------


def test_cadastra_obra_com_metadados_oficiais(sessao):
    with patch(
        "backend.app.catalogo.consultar_obra_por_id",
        return_value=DADOS_OFICIAIS.copy(),
    ) as consulta:
        obra = obter_ou_registrar_obra_oficial(
            sessao,
            MBID_TESTE,
        )

    consulta.assert_called_once_with(MBID_TESTE)

    assert obra.id is not None
    assert obra.id_musicbrainz == MBID_TESTE
    assert obra.titulo == "OK Computer"
    assert obra.artista == "Radiohead"
    assert obra.tipo == "Album"
    assert obra.data_lancamento == "1997-05-21"

    # A funcao nao pode confirmar a transacao sozinha.
    sessao.rollback()

    obras_salvas = sessao.scalars(
        select(Obra)
    ).all()

    assert obras_salvas == []


# -----------------------------------------
# IDENTIFICADOR INVALIDO
# -----------------------------------------


@pytest.mark.parametrize(
    "identificador",
    [
        "album-inventado",
        "",
    ],
)
def test_rejeita_identificador_invalido(
    sessao,
    identificador,
):
    with patch(
        "backend.app.catalogo.consultar_obra_por_id"
    ) as consulta:
        with pytest.raises(
            IdentificadorMusicBrainzInvalido
        ):
            obter_ou_registrar_obra_oficial(
                sessao,
                identificador,
            )

    consulta.assert_not_called()

    assert sessao.scalars(select(Obra)).all() == []


# -----------------------------------------
# OBRA INEXISTENTE
# -----------------------------------------


def test_nao_cadastra_obra_inexistente(sessao):
    with patch(
        "backend.app.catalogo.consultar_obra_por_id",
        return_value=None,
    ):
        with pytest.raises(
            ObraNaoEncontradaNoMusicBrainz
        ):
            obter_ou_registrar_obra_oficial(
                sessao,
                MBID_TESTE,
            )

    assert sessao.scalars(select(Obra)).all() == []


# -----------------------------------------
# FALHA DO SERVICO EXTERNO
# -----------------------------------------


def test_nao_cadastra_se_musicbrainz_falhar(sessao):
    with patch(
        "backend.app.catalogo.consultar_obra_por_id",
        side_effect=httpx.ConnectError(
            "Falha simulada de conexao"
        ),
    ):
        with pytest.raises(FalhaConsultaMusicBrainz):
            obter_ou_registrar_obra_oficial(
                sessao,
                MBID_TESTE,
            )

    assert sessao.scalars(select(Obra)).all() == []


# -----------------------------------------
# METADADOS INCONSISTENTES
# -----------------------------------------


def test_rejeita_metadados_invalidos(sessao):
    dados_invalidos = {
        **DADOS_OFICIAIS,
        "titulo": "",
    }

    with patch(
        "backend.app.catalogo.consultar_obra_por_id",
        return_value=dados_invalidos,
    ):
        with pytest.raises(FalhaConsultaMusicBrainz):
            obter_ou_registrar_obra_oficial(
                sessao,
                MBID_TESTE,
            )

    assert sessao.scalars(select(Obra)).all() == []
