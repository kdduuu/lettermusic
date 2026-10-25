
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from backend.app.database import obter_sessao
from backend.app.main import app
from backend.app.models import Base, Usuario


def test_consultar_perfil_publico():
    motor = create_engine(
        "sqlite+pysqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool
    )

    Base.metadata.create_all(motor)

    with Session(motor) as sessao:
        sessao.add(
            Usuario(
                username="radiohead_fan",
                nome_exibicao="Radiohead Fan",
                email="teste@example.com",
                senha_hash="hash-ficticio"
            )
        )
        sessao.commit()

    def sessao_teste():
        with Session(motor) as sessao:
            yield sessao

    app.dependency_overrides[obter_sessao] = sessao_teste

    try:
        with TestClient(app) as cliente:
            perfil = cliente.get("/usuarios/radiohead_fan")
            assert perfil.status_code == 200

            dados = perfil.json()
            assert dados["username"] == "radiohead_fan"
            assert dados["nome_exibicao"] == "Radiohead Fan"
            assert "email" not in dados
            assert "senha_hash" not in dados

            maiusculas = cliente.get("/usuarios/Radiohead_Fan")
            assert maiusculas.status_code == 200

            inexistente = cliente.get("/usuarios/nao_existe")
            assert inexistente.status_code == 404

    finally:
        app.dependency_overrides.pop(obter_sessao, None)
        motor.dispose()
