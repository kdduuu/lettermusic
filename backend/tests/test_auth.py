
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from backend.app.database import obter_sessao
from backend.app.main import app
from backend.app.models import Base


def test_login_e_usuario_autenticado(monkeypatch):
    monkeypatch.setenv(
        "JWT_SECRET",
        "chave-ficticia-exclusiva-para-testes-123456789"
    )

    motor = create_engine(
        "sqlite+pysqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool
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
                    "username": "teste_login",
                    "nome_exibicao": "Teste Login",
                    "email": "teste-login@example.com",
                    "senha": "SenhaDeTeste#2026"
                }
            )
            assert cadastro.status_code == 201

            login = cliente.post(
                "/auth/login",
                json={
                    "identificador": "teste_login",
                    "senha": "SenhaDeTeste#2026"
                }
            )
            assert login.status_code == 200

            token = login.json()["access_token"]

            perfil = cliente.get(
                "/auth/me",
                headers={"Authorization": f"Bearer {token}"}
            )

            assert perfil.status_code == 200
            assert perfil.json()["username"] == "teste_login"
            assert "senha_hash" not in perfil.json()
            assert "email" not in perfil.json()

            sem_token = cliente.get("/auth/me")
            assert sem_token.status_code == 401

            token_invalido = cliente.get(
                "/auth/me",
                headers={"Authorization": "Bearer token-falso"}
            )
            assert token_invalido.status_code == 401

            senha_errada = cliente.post(
                "/auth/login",
                json={
                    "identificador": "teste_login",
                    "senha": "senha-incorreta"
                }
            )
            assert senha_errada.status_code == 401

    finally:
        app.dependency_overrides.pop(obter_sessao, None)
        motor.dispose()
