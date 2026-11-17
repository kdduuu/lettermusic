"""Testes de contrato e privacidade das capas do perfil publico."""
from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from backend.app.database import obter_sessao
from backend.app.main import app
from backend.app.models import (
    Avaliacao, Base, Favorito, ListaMusical, Obra, ObraOuvida,
    QueroOuvir, Review, Usuario,
)


@pytest.fixture
def ambiente():
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
        app.dependency_overrides.pop(obter_sessao, None)
        motor.dispose()


def novo_usuario(sessao, username):
    usuario = Usuario(
        username=username,
        nome_exibicao=username.title(),
        email=f"{username}@example.com",
        senha_hash="hash-ficticio",
    )
    sessao.add(usuario)
    sessao.flush()
    return usuario


def nova_obra(sessao, numero):
    obra = Obra(
        id_musicbrainz=f"00000000-0000-0000-0000-{numero:012d}",
        titulo=f"Album {numero}",
        artista="Artista",
    )
    sessao.add(obra)
    sessao.flush()
    return obra


def test_destaques_publicos_sem_duplicar_e_sem_expor_biblioteca_privada(ambiente):
    cliente, motor = ambiente
    agora = datetime(2026, 11, 1, tzinfo=timezone.utc)
    with Session(motor) as sessao:
        usuario = novo_usuario(sessao, "alice")
        obra_review = nova_obra(sessao, 1)
        obra_avaliada = nova_obra(sessao, 2)
        obra_privada = nova_obra(sessao, 3)
        sessao.add_all([
            Review(usuario_id=usuario.id, obra_id=obra_review.id,
                   texto="Review publica", criada_em=agora),
            Avaliacao(usuario_id=usuario.id, obra_id=obra_review.id,
                     nota_passos=9, criada_em=agora + timedelta(days=2)),
            Avaliacao(usuario_id=usuario.id, obra_id=obra_avaliada.id,
                     nota_passos=8, criada_em=agora + timedelta(days=1)),
            ObraOuvida(usuario_id=usuario.id, obra_id=obra_privada.id),
            Favorito(usuario_id=usuario.id, obra_id=obra_privada.id),
            QueroOuvir(usuario_id=usuario.id, obra_id=obra_privada.id),
            ListaMusical(usuario_id=usuario.id, titulo="Privada", publica=False),
        ])
        mbid_publico = obra_review.id_musicbrainz
        sessao.commit()

    resposta = cliente.get("/usuarios/ALICE/social")
    assert resposta.status_code == 200
    dados = resposta.json()
    assert [album["titulo"] for album in dados["albuns_recentes"]] == [
        "Album 1", "Album 2",
    ]
    assert dados["albuns_recentes"][0]["id_musicbrainz"] == mbid_publico
    assert dados["reviews_recentes"][0]["id_musicbrainz"] == mbid_publico
    assert dados["estatisticas"] == {"avaliacoes": 2, "reviews": 1, "listas_publicas": 0}
    assert "Album 3" not in str(dados)
    assert "Privada" not in str(dados)
    assert "email" not in dados
    assert "senha_hash" not in dados
    assert "escutas" not in dados
    with Session(motor) as sessao:
        assert len(sessao.scalars(select(Obra)).all()) == 3  # GET nao persistiu nada


def test_destaques_limitados_a_cinco_obras_distintas(ambiente):
    cliente, motor = ambiente
    agora = datetime(2026, 10, 1, tzinfo=timezone.utc)
    with Session(motor) as sessao:
        usuario = novo_usuario(sessao, "bruno")
        for n in range(1, 9):
            obra = nova_obra(sessao, n)
            sessao.add(Review(
                usuario_id=usuario.id, obra_id=obra.id,
                texto=f"Review {n}", criada_em=agora + timedelta(days=n),
            ))
        sessao.commit()

    dados = cliente.get("/usuarios/bruno/social").json()
    assert [item["titulo"] for item in dados["albuns_recentes"]] == [
        "Album 8", "Album 7", "Album 6", "Album 5", "Album 4",
    ]
    assert len(dados["reviews_recentes"]) == 5


def test_destaques_isolados_por_usuario(ambiente):
    cliente, motor = ambiente
    with Session(motor) as sessao:
        um = novo_usuario(sessao, "carlos")
        outro = novo_usuario(sessao, "daniel")
        obra = nova_obra(sessao, 1)
        sessao.add(Avaliacao(usuario_id=outro.id, obra_id=obra.id, nota_passos=10))
        sessao.commit()

    dados = cliente.get("/usuarios/carlos/social").json()
    assert dados["albuns_recentes"] == []
    assert dados["estatisticas"]["avaliacoes"] == 0