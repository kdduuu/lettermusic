from datetime import datetime, timedelta, timezone

import jwt
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from backend.app.database import obter_sessao
from backend.app.main import app
from backend.app.models import Base, Usuario
from backend.app.usuarios import protetor_senhas


@pytest.fixture
def ambiente(monkeypatch):
    chave = "chave-ficticia-exclusiva-para-testes-auth-politicas"
    monkeypatch.setenv("JWT_SECRET", chave)
    monkeypatch.setenv("EMAIL_REQUIRE_VERIFICATION", "false")
    motor = create_engine(
        "sqlite+pysqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(motor)

    with Session(motor) as sessao:
        usuario = Usuario(
            username="politica_teste",
            nome_exibicao="Politica Teste",
            email="politica@example.com",
            senha_hash=protetor_senhas.hash("SenhaDeTeste#2026"),
        )
        sessao.add(usuario)
        sessao.commit()
        usuario_id = usuario.id

    def sessao_teste():
        with Session(motor) as sessao:
            yield sessao

    app.dependency_overrides[obter_sessao] = sessao_teste
    try:
        with TestClient(app) as cliente:
            yield cliente, motor, usuario_id, chave
    finally:
        app.dependency_overrides.pop(obter_sessao, None)
        motor.dispose()


def test_claims_malformadas_sao_rejeitadas(ambiente):
    cliente, _, usuario_id, chave = ambiente
    claims = {
        "sub": str(usuario_id),
        "exp": int((datetime.now(timezone.utc) + timedelta(minutes=5)).timestamp()),
        "ver": 0,
    }

    def consultar(dados):
        token = jwt.encode(dados, chave, algorithm="HS256")
        return cliente.get("/auth/me", headers={"Authorization": f"Bearer {token}"})

    assert consultar(claims).status_code == 200

    for alteracao in (
        {"sub": "2147483648"},
        {"sub": f"0{usuario_id}"},
        {"ver": False},
        {"ver": "0"},
        {"ver": -1},
        {"exp": str(claims["exp"])},
    ):
        assert consultar({**claims, **alteracao}).status_code == 401

    assert consultar({k: v for k, v in claims.items() if k != "ver"}).status_code == 401


def test_sessao_anterior_respeita_confirmacao_obrigatoria(ambiente, monkeypatch):
    cliente, motor, usuario_id, _ = ambiente
    login = cliente.post("/auth/login", json={
        "identificador": "politica_teste",
        "senha": "SenhaDeTeste#2026",
    })
    assert login.status_code == 200
    cabecalho = {"Authorization": f"Bearer {login.json()['access_token']}"}
    assert cliente.get("/auth/me", headers=cabecalho).status_code == 200

    monkeypatch.setenv("EMAIL_REQUIRE_VERIFICATION", "true")
    assert cliente.get("/auth/me", headers=cabecalho).status_code == 403
    assert cliente.patch("/auth/conta", headers=cabecalho, json={
        "nome_exibicao": "Nome Bloqueado",
    }).status_code == 403

    # Simula o estado persistido depois de uma confirmacao valida.
    # O fluxo de consumo de tokens continua coberto pelos testes existentes.
    with Session(motor) as sessao:
        usuario = sessao.get(Usuario, usuario_id)
        assert usuario.nome_exibicao == "Politica Teste"
        usuario.email_confirmado = True
        sessao.commit()

    assert cliente.get("/auth/me", headers=cabecalho).status_code == 200