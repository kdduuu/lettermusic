"""Contratos de leitura social por MBID: sem gravar por simples visualizacao."""
from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from backend.app.auth import obter_usuario_atual
from backend.app.database import obter_sessao
from backend.app.main import app
from backend.app.models import (
    Avaliacao, Base, Escuta, Favorito, Obra, ObraOuvida,
    QueroOuvir, Review, Usuario,
)

MBID = "b1392450-e666-3926-a536-22c65f834433"


@pytest.fixture
def ambiente(monkeypatch):
    monkeypatch.setenv("JWT_SECRET", "segredo-de-teste-de-mais-de-32-caracteres-2026")
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
        app.dependency_overrides.pop(obter_usuario_atual, None)
        app.dependency_overrides.pop(obter_sessao, None)
        motor.dispose()


def adicionar_dados(motor):
    with Session(motor) as sessao:
        a = Usuario(
            username="usuario_a", nome_exibicao="Pessoa A",
            email="a@example.com", senha_hash="hash",
        )
        b = Usuario(
            username="usuario_b", nome_exibicao="Pessoa B",
            email="b@example.com", senha_hash="hash",
        )
        obra = Obra(
            id_musicbrainz=MBID, titulo="OK Computer", artista="Radiohead",
            tipo="Album", data_lancamento="1997-05-21",
        )
        sessao.add_all([a, b, obra])
        sessao.flush()
        sessao.add_all([
            Avaliacao(usuario_id=a.id, obra_id=obra.id, nota_passos=9),
            Avaliacao(usuario_id=b.id, obra_id=obra.id, nota_passos=7),
            Review(usuario_id=a.id, obra_id=obra.id, texto="Um clássico."),
            ObraOuvida(usuario_id=a.id, obra_id=obra.id),
            Favorito(usuario_id=a.id, obra_id=obra.id),
            QueroOuvir(usuario_id=b.id, obra_id=obra.id),
            Escuta(usuario_id=a.id, obra_id=obra.id,
                   ouvida_em=datetime.now(timezone.utc)),
            Escuta(usuario_id=a.id, obra_id=obra.id,
                   ouvida_em=datetime.now(timezone.utc)),
        ])
        sessao.commit()
        return a.id, b.id, obra.id


def test_consulta_social_sem_obra_nao_persiste(ambiente):
    cliente, motor = ambiente
    resposta = cliente.get(f"/catalogo/musicbrainz/{MBID}/social")
    assert resposta.status_code == 200
    assert resposta.json() == {
        "obra_id": None,
        "media_avaliacoes": None,
        "quantidade_avaliacoes": 0,
        "reviews": [],
    }
    with Session(motor) as sessao:
        assert sessao.scalar(select(func.count(Obra.id))) == 0


def test_consulta_privada_exige_autenticacao(ambiente):
    cliente, _ = ambiente
    assert cliente.get(
        f"/catalogo/musicbrainz/{MBID}/meu-estado"
    ).status_code == 401


def test_estado_de_obra_inexistente_nao_cria_registro(ambiente):
    cliente, motor = ambiente
    app.dependency_overrides[obter_usuario_atual] = lambda: Usuario(
        id=99, username="teste", nome_exibicao="Teste",
        email="teste@example.com", senha_hash="hash",
    )
    resposta = cliente.get(f"/catalogo/musicbrainz/{MBID}/meu-estado")
    assert resposta.status_code == 200
    assert resposta.json() == {
        "obra_id": None, "ouvida": False, "favorito": False,
        "quero_ouvir": False, "nota": None, "review": None,
        "quantidade_escutas": 0,
    }
    with Session(motor) as sessao:
        assert sessao.scalar(select(func.count(Obra.id))) == 0


def test_resumo_publico_traz_media_reviews_e_autor(ambiente):
    cliente, motor = ambiente
    _, _, obra_id = adicionar_dados(motor)
    resposta = cliente.get(f"/catalogo/musicbrainz/{MBID}/social")
    assert resposta.status_code == 200
    dados = resposta.json()
    assert dados["obra_id"] == obra_id
    assert dados["quantidade_avaliacoes"] == 2
    assert dados["media_avaliacoes"] == 4.0
    assert len(dados["reviews"]) == 1
    assert dados["reviews"][0]["username"] == "usuario_a"
    assert dados["reviews"][0]["texto"] == "Um clássico."
    assert "senha_hash" not in str(dados)
    assert "email" not in str(dados)


def test_estado_usuario_nao_vaza_interacoes_de_outro(ambiente):
    cliente, motor = ambiente
    a_id, b_id, obra_id = adicionar_dados(motor)

    def estado_de(usuario_id):
        app.dependency_overrides[obter_usuario_atual] = lambda: Usuario(id=usuario_id)
        resposta = cliente.get(f"/catalogo/musicbrainz/{MBID}/meu-estado")
        assert resposta.status_code == 200
        return resposta.json()

    a = estado_de(a_id)
    b = estado_de(b_id)
    assert a == {
        "obra_id": obra_id, "ouvida": True,
        "favorito": True, "quero_ouvir": False,
        "nota": 4.5, "review": "Um clássico.",
        "quantidade_escutas": 2,
    }
    assert b == {
        "obra_id": obra_id, "ouvida": False,
        "favorito": False, "quero_ouvir": True,
        "nota": 3.5, "review": None,
        "quantidade_escutas": 0,
    }


def test_mbid_invalido_recebe_422(ambiente):
    cliente, _ = ambiente
    assert cliente.get("/catalogo/musicbrainz/errado/social").status_code == 422