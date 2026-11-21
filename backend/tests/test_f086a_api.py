import pytest

from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event, select
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from backend.app import limites_login
from backend.app import recuperacao_email as rec
from backend.app.database import obter_sessao
from backend.app.main import app
from backend.app.models import Base, Usuario


SENHA = "SenhaOriginal#2026"


@pytest.fixture
def ambiente(monkeypatch):
    monkeypatch.setenv(
        "JWT_SECRET",
        "chave-descartavel-de-testes-f086a-lettermusic"
    )
    monkeypatch.setenv("EMAIL_REQUIRE_VERIFICATION", "false")
    monkeypatch.setattr(rec, "email_configurado", lambda: False)
    monkeypatch.setattr(limites_login, "_falhas", {})

    motor = create_engine(
        "sqlite+pysqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    @event.listens_for(motor, "connect")
    def ativar_fks(conexao, _):
        conexao.execute("PRAGMA foreign_keys=ON")

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


def criar_usuario(cliente, username):
    cadastro = cliente.post("/usuarios", json={
        "username": username,
        "nome_exibicao": f"Perfil {username}",
        "email": f"{username}@example.com",
        "senha": SENHA,
    })
    assert cadastro.status_code == 201

    login = cliente.post("/auth/login", json={
        "identificador": username,
        "senha": SENHA,
    })
    assert login.status_code == 200

    return {
        "Authorization": f"Bearer {login.json()['access_token']}"
    }


def criar_lista(cliente, cabecalho, titulo, publica=True):
    resposta = cliente.post(
        "/listas",
        headers=cabecalho,
        json={
            "titulo": titulo,
            "descricao": None,
            "publica": publica,
        },
    )
    assert resposta.status_code == 201
    return resposta.json()["id"]


def test_listas_publicas_exibem_autor_sem_dados_privados(ambiente):
    cliente, _ = ambiente
    dono = criar_usuario(cliente, "autor_teste")

    publica = criar_lista(
        cliente, dono, "Discos favoritos", True
    )
    privada = criar_lista(
        cliente, dono, "Lista secreta", False
    )

    resposta = cliente.get("/listas/publicas")
    assert resposta.status_code == 200

    dados = resposta.json()

    assert dados["total"] == 1
    assert len(dados["resultados"]) == 1

    lista = dados["resultados"][0]

    assert lista["id"] == publica
    assert lista["username"] == "autor_teste"
    assert lista["nome_exibicao"] == "Perfil autor_teste"
    assert lista["total_itens"] == 0

    assert "email" not in lista
    assert "senha_hash" not in lista

    assert cliente.get(
        f"/listas/{privada}"
    ).status_code == 404


def test_listas_publicas_tem_paginacao(ambiente):
    cliente, _ = ambiente
    dono = criar_usuario(cliente, "autor_paginacao")

    for numero in range(5):
        criar_lista(cliente, dono, f"Lista {numero}")

    primeira = cliente.get(
        "/listas/publicas?pagina=1&por_pagina=2"
    )
    segunda = cliente.get(
        "/listas/publicas?pagina=2&por_pagina=2"
    )
    terceira = cliente.get(
        "/listas/publicas?pagina=3&por_pagina=2"
    )

    assert primeira.status_code == 200
    assert primeira.json()["total"] == 5
    assert primeira.json()["tem_proxima"] is True
    assert segunda.json()["tem_proxima"] is True
    assert terceira.json()["tem_proxima"] is False

    ids = [
        item["id"]
        for resposta in (primeira, segunda, terceira)
        for item in resposta.json()["resultados"]
    ]

    assert len(ids) == 5
    assert len(set(ids)) == 5

    assert cliente.get(
        "/listas/publicas?por_pagina=100"
    ).status_code == 422


def test_listas_publicas_contam_albuns(ambiente):
    cliente, _ = ambiente
    dono = criar_usuario(cliente, "autor_albuns")
    lista_id = criar_lista(cliente, dono, "Um album")

    adicionar = cliente.post(
        f"/listas/{lista_id}/itens",
        headers=dono,
        json={
            "obra": {
                "id_musicbrainz": (
                    "00000000-0000-0000-0000-000000000001"
                )
            }
        },
    )
    assert adicionar.status_code == 201

    dados = cliente.get("/listas/publicas").json()
    assert dados["resultados"][0]["total_itens"] == 1


def test_troca_manual_invalida_link_de_recuperacao(ambiente):
    cliente, motor = ambiente
    cabecalho = criar_usuario(cliente, "troca_segura")

    with Session(motor) as sessao:
        usuario = sessao.scalar(
            select(Usuario).where(
                Usuario.username == "troca_segura"
            )
        )
        assert usuario is not None
        link_antigo = rec.emitir_token(
            sessao, usuario, "senha"
        )

    resposta = cliente.post(
        "/auth/senha",
        headers=cabecalho,
        json={
            "senha_atual": SENHA,
            "senha_nova": "SenhaNovaSegura#2026",
        },
    )
    assert resposta.status_code == 204

    reutilizacao = cliente.post(
        "/auth/senha/redefinir",
        json={
            "token": link_antigo,
            "senha_nova": "SenhaIndesejada#2026",
        },
    )

    assert reutilizacao.status_code == 400

    assert cliente.get(
        "/auth/me",
        headers=cabecalho,
    ).status_code == 401

    novo_login = cliente.post("/auth/login", json={
        "identificador": "troca_segura",
        "senha": "SenhaNovaSegura#2026",
    })
    assert novo_login.status_code == 200
