import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from backend.app import limites_http, recuperacao_email, rotas_conta
from backend.app.database import obter_sessao
from backend.app.main import app
from backend.app.models import Base
from sqlalchemy.exc import SQLAlchemyError


SENHA = "SenhaOriginal#2026"
NOVA = "NovaSenhaForte#2026"


@pytest.fixture
def ambiente(monkeypatch):
    monkeypatch.setenv("JWT_SECRET", "chave-descartavel-testes-operacoes-sensiveis-2026")
    monkeypatch.setenv("EMAIL_REQUIRE_VERIFICATION", "false")
    monkeypatch.setattr(recuperacao_email, "email_configurado", lambda: False)
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
            yield cliente
    finally:
        app.dependency_overrides.pop(obter_sessao, None)
        motor.dispose()


def cadastrar(cliente, nome):
    resposta = cliente.post("/usuarios", json={
        "username": nome,
        "nome_exibicao": nome,
        "email": f"{nome}@example.com",
        "senha": SENHA,
    })
    assert resposta.status_code == 201
    return entrar(cliente, nome)


def entrar(cliente, nome):
    resposta = cliente.post("/auth/login", json={
        "identificador": nome,
        "senha": SENHA,
    })
    assert resposta.status_code == 200
    return {"Authorization": f"Bearer {resposta.json()['access_token']}"}


def trocar(cliente, cabecalho, atual):
    return cliente.post("/auth/senha", headers=cabecalho, json={
        "senha_atual": atual,
        "senha_nova": NOVA,
    })


def excluir(cliente, cabecalho, atual):
    return cliente.request("DELETE", "/auth/conta", headers=cabecalho, json={
        "senha_atual": atual,
    })


def test_limite_compartilhado_e_isolado_por_usuario(ambiente, monkeypatch):
    cliente = ambiente
    monkeypatch.setattr(rotas_conta, "LIMITE_OPERACOES_SENSIVEIS", 2)
    alice = cadastrar(cliente, "alice_sensivel")
    bob = cadastrar(cliente, "bob_sensivel")

    assert trocar(cliente, alice, "SenhaIncorreta#2026").status_code == 400
    assert excluir(cliente, alice, "SenhaIncorreta#2026").status_code == 400

    # Um novo login nao reinicia o contador das operacoes sensiveis.
    alice = entrar(cliente, "alice_sensivel")
    bloqueio = trocar(cliente, alice, SENHA)
    assert bloqueio.status_code == 429
    assert 1 <= int(bloqueio.headers["Retry-After"]) <= 300
    assert excluir(cliente, alice, SENHA).status_code == 429
    assert cliente.get("/auth/conta", headers=alice).status_code == 200

    # O limite de Alice nao impede uma operacao legitima de Bob.
    assert trocar(cliente, bob, SENHA).status_code == 204
    assert cliente.get("/auth/me", headers=bob).status_code == 401


def test_falha_do_limitador_impede_operacao_sensivel(ambiente, monkeypatch):
    cliente = ambiente
    cabecalho = cadastrar(cliente, "falha_limitador")

    def indisponivel(*args, **kwargs):
        raise SQLAlchemyError("falha simulada")

    with monkeypatch.context() as contexto:
        contexto.setattr(limites_http, "reservar", indisponivel)
        assert trocar(cliente, cabecalho, SENHA).status_code == 503
        assert excluir(cliente, cabecalho, SENHA).status_code == 503

    assert cliente.get("/auth/conta", headers=cabecalho).status_code == 200
    assert trocar(cliente, cabecalho, SENHA).status_code == 204