from datetime import datetime, timedelta, timezone

from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from backend.app.database import obter_sessao
from backend.app.main import app
from backend.app.models import Base, Escuta, Obra, Usuario
from backend.app.usuarios import protetor_senhas


def test_biblioteca_acessa_registros_apos_pagina_1(monkeypatch):
    monkeypatch.setenv(
        "JWT_SECRET",
        "chave-descartavel-para-teste-paginacao-lettermusic",
    )
    monkeypatch.setenv(
        "EMAIL_REQUIRE_VERIFICATION", "false"
    )

    motor = create_engine(
        "sqlite+pysqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    @event.listens_for(motor, "connect")
    def habilitar_fks(conexao, _):
        conexao.execute("PRAGMA foreign_keys=ON")

    Base.metadata.create_all(motor)

    with Session(motor) as sessao:
        usuario = Usuario(
            username="paginacao_teste",
            nome_exibicao="Teste de paginacao",
            email="paginacao@example.com",
            senha_hash=protetor_senhas.hash("SenhaSegura#2026"),
        )

        obra = Obra(
            id_musicbrainz="00000000-0000-0000-0000-000000000001",
            titulo="Album de teste",
            artista="Artista ficticio",
            tipo="Album",
        )

        sessao.add_all([usuario, obra])
        sessao.flush()

        origem = datetime(
            2026, 1, 1, tzinfo=timezone.utc
        )

        for numero in range(21):
            sessao.add(Escuta(
                usuario_id=usuario.id,
                obra_id=obra.id,
                ouvida_em=origem + timedelta(minutes=numero),
            ))

        sessao.commit()

    def sessao_teste():
        with Session(motor) as sessao:
            yield sessao

    app.dependency_overrides[obter_sessao] = sessao_teste

    try:
        with TestClient(app) as cliente:
            assert cliente.get(
                "/interacoes/escutas"
            ).status_code == 401

            login = cliente.post(
                "/auth/login",
                json={
                    "identificador": "paginacao_teste",
                    "senha": "SenhaSegura#2026",
                },
            )

            assert login.status_code == 200

            cabecalho = {
                "Authorization": (
                    f"Bearer {login.json()['access_token']}"
                )
            }

            primeira = cliente.get(
                "/interacoes/escutas?pagina=1&por_pagina=20",
                headers=cabecalho,
            )
            segunda = cliente.get(
                "/interacoes/escutas?pagina=2&por_pagina=20",
                headers=cabecalho,
            )

            assert primeira.status_code == 200
            assert segunda.status_code == 200

            itens1 = primeira.json()
            itens2 = segunda.json()

            assert len(itens1) == 20
            assert len(itens2) == 1

            ids1 = {item["id"] for item in itens1}
            ids2 = {item["id"] for item in itens2}

            assert not ids1.intersection(ids2)
            assert all(
                item["titulo"] == "Album de teste"
                for item in itens1 + itens2
            )
    finally:
        app.dependency_overrides.pop(obter_sessao, None)
        motor.dispose()
