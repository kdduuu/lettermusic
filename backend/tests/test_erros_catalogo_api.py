
from unittest.mock import patch

import httpx
import pytest

from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from backend.app.database import obter_sessao
from backend.app.main import app
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
# AMBIENTE ISOLADO
# -----------------------------------------


@pytest.fixture
def ambiente(monkeypatch):
    """Prepara API, autenticacao e banco temporario."""

    monkeypatch.setenv(
        "JWT_SECRET",
        "chave-ficticia-exclusiva-para-testes-123456789",
    )

    motor = create_engine(
        "sqlite+pysqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    Base.metadata.create_all(motor)

    def sessao_teste():
        with Session(motor) as sessao:
            yield sessao

    app.dependency_overrides[obter_sessao] = sessao_teste

    try:
        with TestClient(app) as cliente:
            cadastro = cliente.post(
                "/usuarios",
                json={
                    "username": "usuario_catalogo",
                    "nome_exibicao": "Usuario de teste",
                    "email": "catalogo@example.com",
                    "senha": "SenhaDeTeste#2026",
                },
            )

            assert cadastro.status_code == 201

            login = cliente.post(
                "/auth/login",
                json={
                    "identificador": "usuario_catalogo",
                    "senha": "SenhaDeTeste#2026",
                },
            )

            assert login.status_code == 200

            token = login.json()["access_token"]

            headers = {
                "Authorization": f"Bearer {token}",
            }

            yield cliente, motor, headers

    finally:
        app.dependency_overrides.pop(
            obter_sessao,
            None,
        )
        motor.dispose()


def adicionar_favorito(
    cliente,
    headers,
    identificador,
    titulo="Titulo informado pelo cliente",
):
    """Envia uma obra para o fluxo real da API."""

    return cliente.post(
        "/biblioteca/favoritos",
        json={
            "obra": {
                "id_musicbrainz": identificador,
                "titulo": titulo,
                "artista": "Artista informado pelo cliente",
                "tipo": "Album",
            }
        },
        headers=headers,
    )


# -----------------------------------------
# ID INVALIDO
# -----------------------------------------


def test_id_invalido_retorna_422(ambiente):
    cliente, motor, headers = ambiente

    resposta = adicionar_favorito(
        cliente,
        headers,
        "album-inventado",
    )

    assert resposta.status_code == 422
    assert resposta.json() == {
        "detail": "ID MusicBrainz invalido."
    }

    with Session(motor) as sessao:
        assert sessao.scalars(select(Obra)).all() == []


# -----------------------------------------
# OBRA INEXISTENTE
# -----------------------------------------


def test_obra_inexistente_retorna_404(ambiente):
    cliente, motor, headers = ambiente

    with patch(
        "backend.app.catalogo.consultar_obra_por_id",
        return_value=None,
    ):
        resposta = adicionar_favorito(
            cliente,
            headers,
            MBID_TESTE,
        )

    assert resposta.status_code == 404
    assert resposta.json() == {
        "detail": "Obra nao encontrada no MusicBrainz."
    }

    with Session(motor) as sessao:
        assert sessao.scalars(select(Obra)).all() == []


# -----------------------------------------
# FALHA DO SERVICO EXTERNO
# -----------------------------------------


def test_falha_musicbrainz_retorna_502(ambiente):
    cliente, motor, headers = ambiente

    with patch(
        "backend.app.catalogo.consultar_obra_por_id",
        side_effect=httpx.ConnectError(
            "Falha simulada de conexao"
        ),
    ):
        resposta = adicionar_favorito(
            cliente,
            headers,
            MBID_TESTE,
        )

    assert resposta.status_code == 502
    assert resposta.json() == {
        "detail": (
            "Nao foi possivel validar a obra "
            "no MusicBrainz."
        )
    }

    with Session(motor) as sessao:
        assert sessao.scalars(select(Obra)).all() == []


# -----------------------------------------
# METADADOS OFICIAIS
# -----------------------------------------


def test_api_ignora_metadados_inventados(ambiente):
    cliente, motor, headers = ambiente

    with patch(
        "backend.app.catalogo.consultar_obra_por_id",
        return_value=DADOS_OFICIAIS.copy(),
    ):
        resposta = adicionar_favorito(
            cliente,
            headers,
            MBID_TESTE,
            titulo="Album inventado",
        )

    assert resposta.status_code == 201

    with Session(motor) as sessao:
        obra = sessao.scalar(
            select(Obra).where(
                Obra.id_musicbrainz == MBID_TESTE
            )
        )

        assert obra is not None
        assert obra.titulo == "OK Computer"
        assert obra.artista == "Radiohead"
        assert obra.tipo == "Album"
        assert obra.data_lancamento == "1997-05-21"
