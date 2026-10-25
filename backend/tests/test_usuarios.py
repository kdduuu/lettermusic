
from fastapi.testclient import TestClient
from pwdlib import PasswordHash
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from backend.app.database import obter_sessao
from backend.app.main import app
from backend.app.models import Base, Usuario


def test_cadastro_usuario():
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

    dados = {
        "username": "radiohead_fan",
        "nome_exibicao": "Radiohead Fan",
        "email": "radioheadfan@example.com",
        "senha": "SenhaDeTeste#2026"
    }

    try:
        with TestClient(app) as cliente:
            resposta = cliente.post("/usuarios", json=dados)

            assert resposta.status_code == 201
            assert resposta.json()["username"] == "radiohead_fan"
            assert "senha" not in resposta.json()
            assert "senha_hash" not in resposta.json()
            assert "email" not in resposta.json()

            with Session(motor) as sessao:
                usuario = sessao.scalar(
                    select(Usuario).where(
                        Usuario.username == "radiohead_fan"
                    )
                )

                assert usuario is not None
                assert usuario.senha_hash != dados["senha"]
                assert PasswordHash.recommended().verify(
                    dados["senha"], usuario.senha_hash
                )

            repetida = cliente.post("/usuarios", json=dados)
            assert repetida.status_code == 409

    finally:
        app.dependency_overrides.pop(obter_sessao, None)
        motor.dispose()
