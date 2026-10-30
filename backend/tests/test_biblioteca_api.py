
import pytest

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from backend.app.database import obter_sessao
from backend.app.main import app
from backend.app.models import Base


CAMINHOS = [
    "/biblioteca/favoritos",
    "/biblioteca/quero-ouvir",
]

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
    """Cria um banco temporario exclusivo para cada teste."""

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
            yield cliente
    finally:
        app.dependency_overrides.pop(obter_sessao, None)
        motor.dispose()


def autenticar(cliente, username):
    """Cadastra um usuario e retorna sua autenticacao."""

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


def adicionar(cliente, caminho, headers):
    """Adiciona OK Computer a uma colecao."""

    return cliente.post(
        caminho,
        json={"obra": OBRA_TESTE},
        headers=headers,
    )


# -----------------------------------------
# ADICIONAR, LISTAR E REMOVER
# -----------------------------------------


@pytest.mark.parametrize("caminho", CAMINHOS)
def test_adicionar_listar_e_remover(ambiente, caminho):
    cliente = ambiente
    headers = autenticar(cliente, "usuario_um")

    criacao = adicionar(cliente, caminho, headers)

    assert criacao.status_code == 201

    obra_id = criacao.json()["obra_id"]

    assert obra_id > 0
    assert criacao.json()["adicionado_em"] is not None

    consulta = cliente.get(caminho, headers=headers)

    assert consulta.status_code == 200
    assert len(consulta.json()) == 1
    assert consulta.json()[0]["obra_id"] == obra_id

    exclusao = cliente.delete(
        f"{caminho}/{obra_id}",
        headers=headers,
    )

    assert exclusao.status_code == 204
    assert exclusao.content == b""

    consulta_final = cliente.get(caminho, headers=headers)

    assert consulta_final.json() == []


# -----------------------------------------
# IMPEDIR DUPLICIDADES
# -----------------------------------------


@pytest.mark.parametrize("caminho", CAMINHOS)
def test_nao_permite_duplicidade(ambiente, caminho):
    cliente = ambiente
    headers = autenticar(cliente, "usuario_dois")

    primeira = adicionar(cliente, caminho, headers)
    segunda = adicionar(cliente, caminho, headers)

    assert primeira.status_code == 201
    assert segunda.status_code == 409

    consulta = cliente.get(caminho, headers=headers)

    assert len(consulta.json()) == 1


# -----------------------------------------
# PRIVACIDADE ENTRE USUARIOS
# -----------------------------------------


@pytest.mark.parametrize("caminho", CAMINHOS)
def test_usuario_nao_altera_colecao_alheia(
    ambiente,
    caminho,
):
    cliente = ambiente

    headers_a = autenticar(cliente, "usuario_a")
    headers_b = autenticar(cliente, "usuario_b")

    criacao = adicionar(cliente, caminho, headers_a)

    assert criacao.status_code == 201

    obra_id = criacao.json()["obra_id"]

    consulta_b = cliente.get(
        caminho,
        headers=headers_b,
    )

    assert consulta_b.json() == []

    exclusao_b = cliente.delete(
        f"{caminho}/{obra_id}",
        headers=headers_b,
    )

    assert exclusao_b.status_code == 404

    consulta_a = cliente.get(
        caminho,
        headers=headers_a,
    )

    assert len(consulta_a.json()) == 1


# -----------------------------------------
# NAO REGISTRAR ESCUTAS
# -----------------------------------------


@pytest.mark.parametrize("caminho", CAMINHOS)
def test_biblioteca_nao_cria_escuta(
    ambiente,
    caminho,
):
    cliente = ambiente
    headers = autenticar(cliente, "usuario_tres")

    criacao = adicionar(cliente, caminho, headers)

    assert criacao.status_code == 201

    escutas = cliente.get(
        "/interacoes/escutas",
        headers=headers,
    )

    ouvidas = cliente.get(
        "/interacoes/obras-ouvidas",
        headers=headers,
    )

    assert escutas.json() == []
    assert ouvidas.json() == []


# -----------------------------------------
# ROTAS PROTEGIDAS
# -----------------------------------------


@pytest.mark.parametrize("caminho", CAMINHOS)
def test_biblioteca_exige_login(ambiente, caminho):
    cliente = ambiente

    criacao = cliente.post(
        caminho,
        json={"obra": OBRA_TESTE},
    )

    consulta = cliente.get(caminho)

    exclusao = cliente.delete(f"{caminho}/1")

    assert criacao.status_code == 401
    assert consulta.status_code == 401
    assert exclusao.status_code == 401


# -----------------------------------------
# COLECOES INDEPENDENTES
# -----------------------------------------


def test_favoritos_e_quero_ouvir_sao_independentes(
    ambiente,
):
    cliente = ambiente
    headers = autenticar(cliente, "usuario_quatro")

    favorito = adicionar(
        cliente,
        "/biblioteca/favoritos",
        headers,
    )

    quero_ouvir = adicionar(
        cliente,
        "/biblioteca/quero-ouvir",
        headers,
    )

    assert favorito.status_code == 201
    assert quero_ouvir.status_code == 201

    obra_id = favorito.json()["obra_id"]

    assert quero_ouvir.json()["obra_id"] == obra_id

    exclusao = cliente.delete(
        f"/biblioteca/favoritos/{obra_id}",
        headers=headers,
    )

    assert exclusao.status_code == 204

    favoritos = cliente.get(
        "/biblioteca/favoritos",
        headers=headers,
    )

    pendentes = cliente.get(
        "/biblioteca/quero-ouvir",
        headers=headers,
    )

    assert favoritos.json() == []
    assert len(pendentes.json()) == 1
