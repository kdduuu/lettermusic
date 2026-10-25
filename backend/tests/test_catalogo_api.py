from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from backend.app.database import obter_sessao
from backend.app.main import app
from backend.app.models import Base, Obra


def test_catalogo_lista_obras_salvas():
    motor = create_engine(
        "sqlite+pysqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool
    )

    Base.metadata.create_all(motor)

    with Session(motor) as sessao:
        sessao.add(
            Obra(
                id_musicbrainz="teste-123",
                titulo="OK Computer",
                artista="Radiohead",
                tipo="Album",
                data_lancamento="1997-05-21"
            )
        )
        sessao.commit()

    def sessao_teste():
        with Session(motor) as sessao:
            yield sessao

    # Substitui a conexão real pelo banco de teste.
    app.dependency_overrides[obter_sessao] = sessao_teste

    try:
        with TestClient(app) as cliente:
            resposta = cliente.get("/catalogo/obras")

        assert resposta.status_code == 200
        assert len(resposta.json()["resultados"]) == 1
        assert resposta.json()["resultados"][0]["titulo"] == "OK Computer"
        assert resposta.json()["resultados"][0]["artista"] == "Radiohead"

    finally:
        app.dependency_overrides.pop(obter_sessao, None)
        motor.dispose()
