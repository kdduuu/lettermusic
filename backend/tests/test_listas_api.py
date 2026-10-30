
import pytest

from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event, select
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from backend.app.database import obter_sessao
from backend.app.main import app
from backend.app.models import Base, Escuta, ItemLista, ListaMusical, Obra


SENHA_TESTE = "SenhaDeTeste#2026"

# IDs ficticios, utilizados somente no banco de testes.
OBRAS = [
    {
        "id_musicbrainz": "00000000-0000-0000-0000-000000000001",
        "titulo": "Disco A",
        "artista": "Artista A",
        "tipo": "Album",
    },
    {
        "id_musicbrainz": "00000000-0000-0000-0000-000000000002",
        "titulo": "Disco B",
        "artista": "Artista B",
        "tipo": "Album",
    },
    {
        "id_musicbrainz": "00000000-0000-0000-0000-000000000003",
        "titulo": "Disco C",
        "artista": "Artista C",
        "tipo": "Album",
    },
]


@pytest.fixture
def ambiente(monkeypatch):
    """Cria um banco temporario para cada teste."""

    monkeypatch.setenv(
        "JWT_SECRET",
        "chave-ficticia-exclusiva-para-testes-123456789",
    )

    motor = create_engine(
        "sqlite+pysqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    @event.listens_for(motor, "connect")
    def ativar_chaves_estrangeiras(conexao, _):
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


def autenticar(cliente, username):
    """Cadastra um usuario e retorna seu cabecalho JWT."""

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


def criar_lista(cliente, headers, publica=True):
    return cliente.post(
        "/listas",
        json={
            "titulo": "Shoegaze Essentials",
            "descricao": "Meus discos favoritos.",
            "publica": publica,
        },
        headers=headers,
    )


def adicionar_album(cliente, headers, lista_id, indice):
    return cliente.post(
        f"/listas/{lista_id}/itens",
        json={"obra": OBRAS[indice]},
        headers=headers,
    )


# -----------------------------------------
# CRIACAO E CONSULTA
# -----------------------------------------


def test_criar_e_consultar_lista_publica(ambiente):
    cliente, _ = ambiente
    headers = autenticar(cliente, "usuario_um")

    criacao = criar_lista(cliente, headers)

    assert criacao.status_code == 201
    assert criacao.json()["titulo"] == "Shoegaze Essentials"
    assert criacao.json()["publica"] is True

    lista_id = criacao.json()["id"]

    minhas = cliente.get("/listas/minhas", headers=headers)
    publica = cliente.get(f"/listas/{lista_id}")

    assert minhas.status_code == 200
    assert len(minhas.json()) == 1
    assert publica.status_code == 200


# -----------------------------------------
# PRIVACIDADE
# -----------------------------------------


def test_lista_privada_so_e_visivel_ao_dono(ambiente):
    cliente, _ = ambiente

    dono = autenticar(cliente, "dono_lista")
    outro = autenticar(cliente, "outro_usuario")

    criacao = criar_lista(cliente, dono, publica=False)
    lista_id = criacao.json()["id"]

    assert cliente.get(f"/listas/{lista_id}").status_code == 404
    assert cliente.get(f"/listas/{lista_id}/itens").status_code == 404

    minha = cliente.get(
        f"/listas/minhas/{lista_id}",
        headers=dono,
    )

    meus_itens = cliente.get(
        f"/listas/minhas/{lista_id}/itens",
        headers=dono,
    )

    acesso_alheio = cliente.get(
        f"/listas/minhas/{lista_id}",
        headers=outro,
    )

    assert minha.status_code == 200
    assert meus_itens.status_code == 200
    assert meus_itens.json() == []
    assert acesso_alheio.status_code == 404


# -----------------------------------------
# EDICAO
# -----------------------------------------


def test_editar_lista_e_alterar_privacidade(ambiente):
    cliente, _ = ambiente
    headers = autenticar(cliente, "usuario_editor")

    criacao = criar_lista(cliente, headers)
    lista_id = criacao.json()["id"]

    edicao = cliente.put(
        f"/listas/{lista_id}",
        json={
            "titulo": "  Discos para ouvir a noite  ",
            "descricao": "  Minha selecao pessoal.  ",
            "publica": False,
        },
        headers=headers,
    )

    assert edicao.status_code == 200
    assert edicao.json()["titulo"] == "Discos para ouvir a noite"
    assert edicao.json()["descricao"] == "Minha selecao pessoal."
    assert edicao.json()["publica"] is False
    assert edicao.json()["atualizada_em"] is not None

    assert cliente.get(f"/listas/{lista_id}").status_code == 404


def test_outro_usuario_nao_edita_nem_exclui_lista(ambiente):
    cliente, _ = ambiente

    dono = autenticar(cliente, "usuario_dono")
    outro = autenticar(cliente, "usuario_visitante")

    lista_id = criar_lista(cliente, dono).json()["id"]

    edicao = cliente.put(
        f"/listas/{lista_id}",
        json={
            "titulo": "Lista alterada",
            "descricao": None,
            "publica": False,
        },
        headers=outro,
    )

    exclusao = cliente.delete(
        f"/listas/{lista_id}",
        headers=outro,
    )

    assert edicao.status_code == 404
    assert exclusao.status_code == 404
    assert cliente.get(f"/listas/{lista_id}").status_code == 200


# -----------------------------------------
# VALIDACAO DE CAMPOS
# -----------------------------------------


def test_dados_invalidos_sao_rejeitados(ambiente):
    cliente, _ = ambiente
    headers = autenticar(cliente, "usuario_validacao")

    titulo_vazio = cliente.post(
        "/listas",
        json={"titulo": "   ", "publica": True},
        headers=headers,
    )

    titulo_longo = cliente.post(
        "/listas",
        json={"titulo": "A" * 121},
        headers=headers,
    )

    assert titulo_vazio.status_code == 422
    assert titulo_longo.status_code == 422

    lista_id = criar_lista(cliente, headers).json()["id"]

    edicao_incompleta = cliente.put(
        f"/listas/{lista_id}",
        json={"titulo": "Outro titulo"},
        headers=headers,
    )

    assert edicao_incompleta.status_code == 422


# -----------------------------------------
# ALBUNS E DUPLICIDADES
# -----------------------------------------


def test_adicionar_album_e_impedir_duplicidade(ambiente):
    cliente, _ = ambiente
    headers = autenticar(cliente, "usuario_albuns")

    lista_id = criar_lista(cliente, headers).json()["id"]

    primeiro = adicionar_album(cliente, headers, lista_id, 0)
    repetido = adicionar_album(cliente, headers, lista_id, 0)

    assert primeiro.status_code == 201
    assert primeiro.json()["posicao"] == 1
    assert repetido.status_code == 409

    itens = cliente.get(f"/listas/{lista_id}/itens")

    assert itens.status_code == 200
    assert len(itens.json()) == 1

    escutas = cliente.get(
        "/interacoes/escutas",
        headers=headers,
    )

    assert escutas.json() == []


# -----------------------------------------
# REORDENACAO E REMOCAO
# -----------------------------------------


def test_reordenar_e_remover_albuns(ambiente):
    cliente, _ = ambiente
    headers = autenticar(cliente, "usuario_ordem")

    lista_id = criar_lista(cliente, headers).json()["id"]

    respostas = [
        adicionar_album(cliente, headers, lista_id, indice)
        for indice in range(3)
    ]

    assert all(r.status_code == 201 for r in respostas)

    ids = [r.json()["obra_id"] for r in respostas]

    mover = cliente.patch(
        f"/listas/{lista_id}/itens/{ids[2]}",
        json={"nova_posicao": 1},
        headers=headers,
    )

    assert mover.status_code == 200
    assert mover.json()["posicao"] == 1

    itens = cliente.get(f"/listas/{lista_id}/itens").json()

    assert [item["obra_id"] for item in itens] == [
        ids[2], ids[0], ids[1]
    ]

    remover = cliente.delete(
        f"/listas/{lista_id}/itens/{ids[0]}",
        headers=headers,
    )

    assert remover.status_code == 204

    restantes = cliente.get(
        f"/listas/{lista_id}/itens"
    ).json()

    assert [item["obra_id"] for item in restantes] == [
        ids[2], ids[1]
    ]

    assert [item["posicao"] for item in restantes] == [1, 2]


def test_posicoes_invalidas_sao_rejeitadas(ambiente):
    cliente, _ = ambiente
    headers = autenticar(cliente, "usuario_posicao")

    lista_id = criar_lista(cliente, headers).json()["id"]
    obra_id = adicionar_album(
        cliente, headers, lista_id, 0
    ).json()["obra_id"]

    for posicao in [0, -1, 99]:
        resposta = cliente.patch(
            f"/listas/{lista_id}/itens/{obra_id}",
            json={"nova_posicao": posicao},
            headers=headers,
        )

        assert resposta.status_code == 422


# -----------------------------------------
# PERMISSOES DOS ITENS
# -----------------------------------------


def test_outro_usuario_nao_modifica_albuns(ambiente):
    cliente, _ = ambiente

    dono = autenticar(cliente, "dono_albuns")
    outro = autenticar(cliente, "visitante_albuns")

    lista_id = criar_lista(cliente, dono).json()["id"]

    primeiro = adicionar_album(cliente, dono, lista_id, 0)
    obra_id = primeiro.json()["obra_id"]

    adicao_alheia = adicionar_album(
        cliente, outro, lista_id, 1
    )

    edicao_alheia = cliente.patch(
        f"/listas/{lista_id}/itens/{obra_id}",
        json={"nova_posicao": 1},
        headers=outro,
    )

    exclusao_alheia = cliente.delete(
        f"/listas/{lista_id}/itens/{obra_id}",
        headers=outro,
    )

    assert adicao_alheia.status_code == 404
    assert edicao_alheia.status_code == 404
    assert exclusao_alheia.status_code == 404

    itens = cliente.get(f"/listas/{lista_id}/itens")

    assert len(itens.json()) == 1


# -----------------------------------------
# EXCLUSAO SEM AFETAR O CATALOGO
# -----------------------------------------


def test_excluir_lista_preserva_catalogo(ambiente):
    cliente, motor = ambiente
    headers = autenticar(cliente, "usuario_exclusao")

    lista_id = criar_lista(cliente, headers).json()["id"]

    criacao = adicionar_album(
        cliente, headers, lista_id, 0
    )

    assert criacao.status_code == 201

    exclusao = cliente.delete(
        f"/listas/{lista_id}",
        headers=headers,
    )

    assert exclusao.status_code == 204
    assert cliente.get(f"/listas/{lista_id}").status_code == 404

    with Session(motor) as sessao:
        assert sessao.scalars(select(ListaMusical)).all() == []
        assert sessao.scalars(select(ItemLista)).all() == []
        assert len(sessao.scalars(select(Obra)).all()) == 1
        assert sessao.scalars(select(Escuta)).all() == []


# -----------------------------------------
# AUTENTICACAO
# -----------------------------------------


def test_rotas_privadas_exigem_login(ambiente):
    cliente, _ = ambiente

    criacao = cliente.post(
        "/listas",
        json={"titulo": "Lista sem login"},
    )

    minhas = cliente.get("/listas/minhas")

    edicao = cliente.put(
        "/listas/1",
        json={
            "titulo": "Teste",
            "descricao": None,
            "publica": True,
        },
    )

    exclusao = cliente.delete("/listas/1")

    assert criacao.status_code == 401
    assert minhas.status_code == 401
    assert edicao.status_code == 401
    assert exclusao.status_code == 401
