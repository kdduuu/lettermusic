
import pytest

from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from backend.app.database import obter_sessao
from backend.app.main import app
from backend.app.models import Base, Escuta, Obra


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
    """Prepara uma API com banco temporario e JWT de teste."""

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


def criar_usuario_e_token(cliente, username):
    """Cadastra um usuario e retorna seu token JWT."""

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


def test_marcar_ouvida_sem_duplicar_ou_criar_escuta(ambiente):
    cliente, _ = ambiente
    headers = criar_usuario_e_token(cliente, "usuario_um")

    dados = {"obra": OBRA_TESTE}

    primeira = cliente.post(
        "/interacoes/obras-ouvidas",
        json=dados,
        headers=headers,
    )

    segunda = cliente.post(
        "/interacoes/obras-ouvidas",
        json=dados,
        headers=headers,
    )

    assert primeira.status_code == 200
    assert segunda.status_code == 200
    assert primeira.json()["id"] == segunda.json()["id"]

    marcacoes = cliente.get(
        "/interacoes/obras-ouvidas",
        headers=headers,
    )

    escutas = cliente.get(
        "/interacoes/escutas",
        headers=headers,
    )

    assert len(marcacoes.json()) == 1
    assert escutas.json() == []


def test_registrar_varias_escutas(ambiente):
    cliente, _ = ambiente
    headers = criar_usuario_e_token(cliente, "usuario_dois")

    primeira = cliente.post(
        "/interacoes/escutas",
        json={
            "obra": OBRA_TESTE,
            "ouvida_em": "2026-10-20T18:00:00-03:00",
        },
        headers=headers,
    )

    segunda = cliente.post(
        "/interacoes/escutas",
        json={"obra": OBRA_TESTE},
        headers=headers,
    )

    assert primeira.status_code == 201
    assert segunda.status_code == 201

    assert primeira.json()["id"] != segunda.json()["id"]
    assert primeira.json()["obra_id"] == segunda.json()["obra_id"]

    historico = cliente.get(
        "/interacoes/escutas",
        headers=headers,
    )

    marcacoes = cliente.get(
        "/interacoes/obras-ouvidas",
        headers=headers,
    )

    assert historico.status_code == 200
    assert len(historico.json()) == 2
    assert len(marcacoes.json()) == 1


def test_autenticacao_e_separacao_entre_usuarios(ambiente):
    cliente, _ = ambiente

    headers_a = criar_usuario_e_token(cliente, "usuario_a")
    headers_b = criar_usuario_e_token(cliente, "usuario_b")

    sem_token = cliente.post(
        "/interacoes/escutas",
        json={"obra": OBRA_TESTE},
    )

    assert sem_token.status_code == 401

    resposta = cliente.post(
        "/interacoes/obras-ouvidas",
        json={"obra": OBRA_TESTE},
        headers=headers_a,
    )

    assert resposta.status_code == 200

    obras_a = cliente.get(
        "/interacoes/obras-ouvidas",
        headers=headers_a,
    )

    obras_b = cliente.get(
        "/interacoes/obras-ouvidas",
        headers=headers_b,
    )

    assert len(obras_a.json()) == 1
    assert obras_b.json() == []

    assert cliente.get(
        "/interacoes/escutas"
    ).status_code == 401

    assert cliente.get(
        "/interacoes/obras-ouvidas"
    ).status_code == 401


def test_data_sem_fuso_horario_e_rejeitada(ambiente):
    cliente, _ = ambiente
    headers = criar_usuario_e_token(cliente, "usuario_tres")

    resposta = cliente.post(
        "/interacoes/escutas",
        json={
            "obra": OBRA_TESTE,
            "ouvida_em": "2026-10-20T18:00:00",
        },
        headers=headers,
    )

    assert resposta.status_code == 422

    historico = cliente.get(
        "/interacoes/escutas",
        headers=headers,
    )

    assert historico.json() == []

    catalogo = cliente.get("/catalogo/obras")
    assert catalogo.json()["resultados"] == []


def test_falha_desfaz_obra_e_escuta(ambiente, monkeypatch):
    cliente, motor = ambiente
    headers = criar_usuario_e_token(cliente, "usuario_quatro")

    def simular_falha(*args, **kwargs):
        raise RuntimeError("Falha simulada")

    with monkeypatch.context() as alteracoes:
        alteracoes.setattr(
            "backend.app.interacoes.garantir_obra_ouvida",
            simular_falha,
        )

        with pytest.raises(RuntimeError):
            cliente.post(
                "/interacoes/escutas",
                json={"obra": OBRA_TESTE},
                headers=headers,
            )

    with Session(motor) as sessao:
        obras = sessao.scalars(select(Obra)).all()
        escutas = sessao.scalars(select(Escuta)).all()

        assert obras == []
        assert escutas == []
