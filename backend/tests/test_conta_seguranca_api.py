import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from backend.app import limites_login
from backend.app.database import obter_sessao
from backend.app.main import app
from backend.app.models import Base


@pytest.fixture
def cliente(monkeypatch):
    monkeypatch.setenv(
        "JWT_SECRET",
        "chave-ficticia-para-testes-de-conta-lettermusic-2026"
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
        with TestClient(app) as c:
            cadastro = c.post("/usuarios", json={
                "username": "conta_segura",
                "nome_exibicao": "Conta Segura",
                "email": "conta-segura@example.com",
                "senha": "SenhaOriginal#2026",
            })
            assert cadastro.status_code == 201
            yield c
    finally:
        app.dependency_overrides.pop(obter_sessao, None)
        motor.dispose()


def login(cliente, senha="SenhaOriginal#2026"):
    return cliente.post("/auth/login", json={
        "identificador": "conta_segura",
        "senha": senha,
    })


def token(cliente):
    resposta = login(cliente)
    assert resposta.status_code == 200
    return resposta.json()["access_token"]


def cabecalho(valor):
    return {"Authorization": f"Bearer {valor}"}


def test_conta_privada_e_edicao(cliente):
    jwt = token(cliente)

    resposta = cliente.get(
        "/auth/conta", headers=cabecalho(jwt)
    )
    assert resposta.status_code == 200
    assert resposta.json()["email"] == "conta-segura@example.com"
    assert "senha_hash" not in resposta.json()

    publico = cliente.get("/usuarios/conta_segura")
    assert "email" not in publico.json()

    edicao = cliente.patch(
        "/auth/conta",
        headers=cabecalho(jwt),
        json={"nome_exibicao": "  Novo Nome  "},
    )
    assert edicao.status_code == 200
    assert edicao.json()["nome_exibicao"] == "Novo Nome"


def test_troca_de_senha_revoga_sessoes(cliente):
    antigo = token(cliente)

    resposta = cliente.post(
        "/auth/senha",
        headers=cabecalho(antigo),
        json={
            "senha_atual": "SenhaOriginal#2026",
            "senha_nova": "NovaSenhaForte#2026",
        },
    )

    assert resposta.status_code == 204
    assert cliente.get(
        "/auth/me", headers=cabecalho(antigo)
    ).status_code == 401

    assert login(cliente).status_code == 401
    novo = login(cliente, "NovaSenhaForte#2026")
    assert novo.status_code == 200

    novo_token = novo.json()["access_token"]

    assert cliente.post(
        "/auth/sessoes/revogar",
        headers=cabecalho(novo_token),
    ).status_code == 204

    assert cliente.get(
        "/auth/me", headers=cabecalho(novo_token)
    ).status_code == 401


def test_limite_de_tentativas_de_login(cliente):
    for _ in range(limites_login.LIMITE_CONTA):
        resposta = cliente.post("/auth/login", json={
            "identificador": "conta_segura",
            "senha": "senha-incorreta",
        })
        assert resposta.status_code == 401

    bloqueio = cliente.post("/auth/login", json={
        "identificador": "conta_segura",
        "senha": "senha-incorreta",
    })

    assert bloqueio.status_code == 429
    assert 1 <= int(bloqueio.headers["Retry-After"]) <= 60
    assert "senha-incorreta" not in bloqueio.text


def test_erro_de_validacao_nao_devolve_senha(cliente):
    senha = "senha-curta"
    resposta = cliente.post("/usuarios", json={
        "username": "novo_usuario",
        "nome_exibicao": "Novo Usuario",
        "email": "novo@example.com",
        "senha": senha,
    })

    assert resposta.status_code == 422
    assert senha not in resposta.text
