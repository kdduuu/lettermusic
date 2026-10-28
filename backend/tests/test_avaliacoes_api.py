
import pytest

from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from backend.app.database import obter_sessao
from backend.app.main import app
from backend.app.models import (
    Avaliacao,
    Base,
    Escuta,
    Obra,
    ObraOuvida,
)


OBRA_TESTE = {
    "id_musicbrainz": "b1392450-e666-3926-a536-22c65f834433",
    "titulo": "OK Computer",
    "artista": "Radiohead",
    "tipo": "Album",
    "data_lancamento": "1997-05-21",
}

SENHA_TESTE = "SenhaDeTeste#2026"


@pytest.fixture
def ambiente(monkeypatch):
    """Cria API e banco temporarios para cada teste."""

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
            yield cliente, motor
    finally:
        app.dependency_overrides.pop(obter_sessao, None)
        motor.dispose()


def autenticar_teste(cliente, username):
    """Cria uma conta e devolve seu cabecalho JWT."""

    cadastro = cliente.post(
        "/usuarios",
        json={
            "username": username,
            "nome_exibicao": "Usuario de teste",
            "email": f"{username}@example.com",
            "senha": SENHA_TESTE,
        },
    )

    assert cadastro.status_code == 201

    login = cliente.post(
        "/auth/login",
        json={
            "identificador": username,
            "senha": SENHA_TESTE,
        },
    )

    assert login.status_code == 200

    token = login.json()["access_token"]

    return {"Authorization": f"Bearer {token}"}


def avaliar(cliente, headers, nota):
    """Envia uma avaliacao para OK Computer."""

    return cliente.post(
        "/interacoes/avaliacoes",
        json={
            "obra": OBRA_TESTE,
            "nota": nota,
        },
        headers=headers,
    )


def test_criar_avaliacao_registra_escuta(ambiente):
    cliente, _ = ambiente
    headers = autenticar_teste(cliente, "usuario_um")

    resposta = avaliar(cliente, headers, 4.5)

    assert resposta.status_code == 201
    assert resposta.json()["nota"] == 4.5

    avaliacoes = cliente.get(
        "/interacoes/avaliacoes",
        headers=headers,
    )

    escutas = cliente.get(
        "/interacoes/escutas",
        headers=headers,
    )

    obras_ouvidas = cliente.get(
        "/interacoes/obras-ouvidas",
        headers=headers,
    )

    assert len(avaliacoes.json()) == 1
    assert len(escutas.json()) == 1
    assert len(obras_ouvidas.json()) == 1


def test_nao_permite_avaliacao_duplicada(ambiente):
    cliente, _ = ambiente
    headers = autenticar_teste(cliente, "usuario_dois")

    primeira = avaliar(cliente, headers, 4.0)
    segunda = avaliar(cliente, headers, 5.0)

    assert primeira.status_code == 201
    assert segunda.status_code == 409

    avaliacoes = cliente.get(
        "/interacoes/avaliacoes",
        headers=headers,
    )

    escutas = cliente.get(
        "/interacoes/escutas",
        headers=headers,
    )

    assert len(avaliacoes.json()) == 1
    assert avaliacoes.json()[0]["nota"] == 4.0
    assert len(escutas.json()) == 1


def test_editar_avaliacao_sem_nova_escuta(ambiente):
    cliente, _ = ambiente
    headers = autenticar_teste(cliente, "usuario_tres")

    primeira = avaliar(cliente, headers, 3.5)
    assert primeira.status_code == 201

    obra_id = primeira.json()["obra_id"]

    edicao = cliente.patch(
        f"/interacoes/avaliacoes/{obra_id}",
        json={"nota": 5.0},
        headers=headers,
    )

    assert edicao.status_code == 200
    assert edicao.json()["nota"] == 5.0
    assert edicao.json()["atualizada_em"] is not None

    avaliacoes = cliente.get(
        "/interacoes/avaliacoes",
        headers=headers,
    )

    escutas = cliente.get(
        "/interacoes/escutas",
        headers=headers,
    )

    assert len(avaliacoes.json()) == 1
    assert avaliacoes.json()[0]["nota"] == 5.0
    assert len(escutas.json()) == 1


def test_media_da_comunidade(ambiente):
    cliente, _ = ambiente

    headers_a = autenticar_teste(cliente, "usuario_a")
    headers_b = autenticar_teste(cliente, "usuario_b")

    primeira = avaliar(cliente, headers_a, 4.5)
    segunda = avaliar(cliente, headers_b, 3.5)

    assert primeira.status_code == 201
    assert segunda.status_code == 201

    obra_id = primeira.json()["obra_id"]

    media = cliente.get(
        f"/interacoes/avaliacoes/{obra_id}/media"
    )

    assert media.status_code == 200
    assert media.json()["quantidade"] == 2
    assert media.json()["media"] == 4.0

    edicao = cliente.patch(
        f"/interacoes/avaliacoes/{obra_id}",
        json={"nota": 5.0},
        headers=headers_a,
    )

    assert edicao.status_code == 200

    media_atualizada = cliente.get(
        f"/interacoes/avaliacoes/{obra_id}/media"
    )

    assert media_atualizada.json()["quantidade"] == 2
    assert media_atualizada.json()["media"] == 4.25

    inexistente = cliente.get(
        "/interacoes/avaliacoes/999/media"
    )

    assert inexistente.status_code == 404


@pytest.mark.parametrize("nota", [0, 4.7, 5.5])
def test_rejeita_notas_invalidas(ambiente, nota):
    cliente, _ = ambiente
    headers = autenticar_teste(cliente, "usuario_quatro")

    resposta = avaliar(cliente, headers, nota)

    assert resposta.status_code == 422

    avaliacoes = cliente.get(
        "/interacoes/avaliacoes",
        headers=headers,
    )

    escutas = cliente.get(
        "/interacoes/escutas",
        headers=headers,
    )

    assert avaliacoes.json() == []
    assert escutas.json() == []


def test_usuario_nao_edita_avaliacao_alheia(ambiente):
    cliente, _ = ambiente

    headers_a = autenticar_teste(cliente, "usuario_cinco")
    headers_b = autenticar_teste(cliente, "usuario_seis")

    primeira = avaliar(cliente, headers_a, 4.5)
    assert primeira.status_code == 201

    obra_id = primeira.json()["obra_id"]

    tentativa = cliente.patch(
        f"/interacoes/avaliacoes/{obra_id}",
        json={"nota": 1.0},
        headers=headers_b,
    )

    assert tentativa.status_code == 404

    avaliacoes_a = cliente.get(
        "/interacoes/avaliacoes",
        headers=headers_a,
    )

    avaliacoes_b = cliente.get(
        "/interacoes/avaliacoes",
        headers=headers_b,
    )

    assert avaliacoes_a.json()[0]["nota"] == 4.5
    assert avaliacoes_b.json() == []

    sem_token = cliente.post(
        "/interacoes/avaliacoes",
        json={"obra": OBRA_TESTE, "nota": 5.0},
    )

    assert sem_token.status_code == 401


def test_falha_desfaz_avaliacao_e_escuta(ambiente, monkeypatch):
    cliente, motor = ambiente
    headers = autenticar_teste(cliente, "usuario_sete")

    def simular_falha(*args, **kwargs):
        raise RuntimeError("Falha simulada")

    with monkeypatch.context() as alteracoes:
        alteracoes.setattr(
            "backend.app.avaliacoes.garantir_obra_ouvida",
            simular_falha,
        )

        with pytest.raises(RuntimeError):
            avaliar(cliente, headers, 4.5)

    with Session(motor) as sessao:
        assert sessao.scalars(select(Obra)).all() == []
        assert sessao.scalars(select(Avaliacao)).all() == []
        assert sessao.scalars(select(Escuta)).all() == []
        assert sessao.scalars(select(ObraOuvida)).all() == []
