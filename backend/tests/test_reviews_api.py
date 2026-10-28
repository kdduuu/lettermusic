
import pytest

from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from backend.app.database import obter_sessao
from backend.app.main import app
from backend.app.models import (
    Base,
    Escuta,
    Obra,
    ObraOuvida,
    Review,
)


OBRA_TESTE = {
    "id_musicbrainz": "b1392450-e666-3926-a536-22c65f834433",
    "titulo": "OK Computer",
    "artista": "Radiohead",
    "tipo": "Album",
    "data_lancamento": "1997-05-21",
}

SENHA_TESTE = "SenhaDeTeste#2026"


@pytest.fixture
def ambiente(monkeypatch):
    """Cria um banco temporario e configura a autenticacao."""

    monkeypatch.setenv(
        "JWT_SECRET",
        "chave-ficticia-exclusiva-para-testes-123456789",
    )

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


def autenticar_teste(cliente, username):
    """Cria usuario e retorna o cabecalho de autenticacao."""

    cadastro = cliente.post(
        "/usuarios",
        json={
            "username": username,
            "nome_exibicao": "Usuario de teste",
            "email": f"{username}@example.com",
            "senha": SENHA_TESTE,
        },
    )

    assert cadastro.status_code == 201

    login = cliente.post(
        "/auth/login",
        json={
            "identificador": username,
            "senha": SENHA_TESTE,
        },
    )

    assert login.status_code == 200

    token = login.json()["access_token"]

    return {"Authorization": f"Bearer {token}"}


def publicar(cliente, headers, texto="Um album excelente."):
    """Publica uma review de OK Computer."""

    return cliente.post(
        "/interacoes/reviews",
        json={
            "obra": OBRA_TESTE,
            "texto": texto,
        },
        headers=headers,
    )


def test_publicar_review_cria_escuta_e_marcacao(ambiente):
    cliente, _ = ambiente
    headers = autenticar_teste(cliente, "usuario_um")

    resposta = publicar(cliente, headers)

    assert resposta.status_code == 201
    assert resposta.json()["texto"] == "Um album excelente."

    minhas = cliente.get(
        "/interacoes/reviews",
        headers=headers,
    )

    escutas = cliente.get(
        "/interacoes/escutas",
        headers=headers,
    )

    ouvidas = cliente.get(
        "/interacoes/obras-ouvidas",
        headers=headers,
    )

    assert len(minhas.json()) == 1
    assert len(escutas.json()) == 1
    assert len(ouvidas.json()) == 1


def test_review_duplicada_retorna_409(ambiente):
    cliente, _ = ambiente
    headers = autenticar_teste(cliente, "usuario_dois")

    primeira = publicar(cliente, headers)
    segunda = publicar(
        cliente,
        headers,
        "Outra opiniao sobre o mesmo album.",
    )

    assert primeira.status_code == 201
    assert segunda.status_code == 409

    minhas = cliente.get(
        "/interacoes/reviews",
        headers=headers,
    )

    escutas = cliente.get(
        "/interacoes/escutas",
        headers=headers,
    )

    assert len(minhas.json()) == 1
    assert len(escutas.json()) == 1


def test_editar_review_sem_nova_escuta(ambiente):
    cliente, _ = ambiente
    headers = autenticar_teste(cliente, "usuario_tres")

    primeira = publicar(cliente, headers)
    obra_id = primeira.json()["obra_id"]

    edicao = cliente.patch(
        f"/interacoes/reviews/{obra_id}",
        json={
            "texto": "Mudei minha opiniao sobre este disco."
        },
        headers=headers,
    )

    assert edicao.status_code == 200
    assert edicao.json()["texto"] == (
        "Mudei minha opiniao sobre este disco."
    )
    assert edicao.json()["atualizada_em"] is not None

    escutas = cliente.get(
        "/interacoes/escutas",
        headers=headers,
    )

    assert len(escutas.json()) == 1


def test_excluir_review_preserva_historico(ambiente):
    cliente, _ = ambiente
    headers = autenticar_teste(cliente, "usuario_quatro")

    primeira = publicar(cliente, headers)
    obra_id = primeira.json()["obra_id"]

    exclusao = cliente.delete(
        f"/interacoes/reviews/{obra_id}",
        headers=headers,
    )

    assert exclusao.status_code == 204
    assert exclusao.content == b""

    minhas = cliente.get(
        "/interacoes/reviews",
        headers=headers,
    )

    escutas = cliente.get(
        "/interacoes/escutas",
        headers=headers,
    )

    assert minhas.json() == []
    assert len(escutas.json()) == 1

    repetir = cliente.delete(
        f"/interacoes/reviews/{obra_id}",
        headers=headers,
    )

    assert repetir.status_code == 404


def test_reviews_publicas_e_permissoes(ambiente):
    cliente, _ = ambiente

    headers_a = autenticar_teste(cliente, "usuario_a")
    headers_b = autenticar_teste(cliente, "usuario_b")

    primeira = publicar(cliente, headers_a)
    assert primeira.status_code == 201

    obra_id = primeira.json()["obra_id"]

    publicas = cliente.get(
        f"/interacoes/reviews/obra/{obra_id}"
    )

    assert publicas.status_code == 200
    assert len(publicas.json()) == 1
    assert publicas.json()[0]["texto"] == "Um album excelente."

    minhas_b = cliente.get(
        "/interacoes/reviews",
        headers=headers_b,
    )

    assert minhas_b.json() == []

    edicao_alheia = cliente.patch(
        f"/interacoes/reviews/{obra_id}",
        json={"texto": "Tentativa indevida."},
        headers=headers_b,
    )

    exclusao_alheia = cliente.delete(
        f"/interacoes/reviews/{obra_id}",
        headers=headers_b,
    )

    assert edicao_alheia.status_code == 404
    assert exclusao_alheia.status_code == 404

    publicas_depois = cliente.get(
        f"/interacoes/reviews/obra/{obra_id}"
    )

    assert len(publicas_depois.json()) == 1
    assert publicas_depois.json()[0]["texto"] == (
        "Um album excelente."
    )


@pytest.mark.parametrize("texto", ["", "   ", "\n\t"])
def test_review_vazia_e_rejeitada(ambiente, texto):
    cliente, motor = ambiente
    headers = autenticar_teste(cliente, "usuario_cinco")

    resposta = publicar(cliente, headers, texto)

    assert resposta.status_code == 422

    with Session(motor) as sessao:
        assert sessao.scalars(select(Review)).all() == []
        assert sessao.scalars(select(Escuta)).all() == []
        assert sessao.scalars(select(Obra)).all() == []


def test_rotas_protegidas_exigem_token(ambiente):
    cliente, _ = ambiente

    criacao = cliente.post(
        "/interacoes/reviews",
        json={
            "obra": OBRA_TESTE,
            "texto": "Minha review.",
        },
    )

    consulta = cliente.get("/interacoes/reviews")

    edicao = cliente.patch(
        "/interacoes/reviews/1",
        json={"texto": "Texto alterado."},
    )

    exclusao = cliente.delete(
        "/interacoes/reviews/1"
    )

    assert criacao.status_code == 401
    assert consulta.status_code == 401
    assert edicao.status_code == 401
    assert exclusao.status_code == 401


def test_falha_desfaz_review_e_escuta(ambiente, monkeypatch):
    cliente, motor = ambiente
    headers = autenticar_teste(cliente, "usuario_seis")

    def simular_falha(*args, **kwargs):
        raise RuntimeError("Falha simulada")

    with monkeypatch.context() as alteracoes:
        alteracoes.setattr(
            "backend.app.reviews.garantir_obra_ouvida",
            simular_falha,
        )

        with pytest.raises(RuntimeError):
            publicar(cliente, headers)

    with Session(motor) as sessao:
        assert sessao.scalars(select(Obra)).all() == []
        assert sessao.scalars(select(Review)).all() == []
        assert sessao.scalars(select(Escuta)).all() == []
        assert sessao.scalars(select(ObraOuvida)).all() == []


def test_obra_inexistente_retorna_404(ambiente):
    cliente, _ = ambiente

    resposta = cliente.get(
        "/interacoes/reviews/obra/999"
    )

    assert resposta.status_code == 404
