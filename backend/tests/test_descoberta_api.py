
import pytest

from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from backend.app.database import obter_sessao
from backend.app.main import app
from backend.app.models import (
    Avaliacao,
    Base,
    Escuta,
    Obra,
    Usuario,
)


@pytest.fixture
def ambiente():
    """Prepara um banco SQLite isolado para cada teste."""

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


def criar_catalogo(sessao):
    """Cria usuarios e discos ficticios para os testes."""

    usuarios = [
        Usuario(
            username=f"usuario_{numero}",
            nome_exibicao=f"Usuario {numero}",
            email=f"usuario_{numero}@example.com",
            senha_hash="hash-ficticio-de-teste",
        )
        for numero in range(1, 3)
    ]

    obras = [
        Obra(
            id_musicbrainz=(
                f"00000000-0000-0000-0000-{numero:012d}"
            ),
            titulo=f"Disco {numero}",
            artista=f"Artista {numero}",
            tipo="Album",
            data_lancamento="2020-01-01",
        )
        for numero in range(1, 4)
    ]

    sessao.add_all(usuarios + obras)
    sessao.flush()

    return usuarios, obras


def adicionar_escutas(sessao, usuario, obra, quantidade):
    """Registra varias escutas de uma mesma obra."""

    for _ in range(quantidade):
        sessao.add(
            Escuta(
                usuario_id=usuario.id,
                obra_id=obra.id,
            )
        )


def adicionar_avaliacao(sessao, usuario, obra, nota):
    """Armazena nota em passos de meia estrela."""

    sessao.add(
        Avaliacao(
            usuario_id=usuario.id,
            obra_id=obra.id,
            nota_passos=int(nota * 2),
        )
    )


# -----------------------------------------
# RANKINGS VAZIOS
# -----------------------------------------


def test_rankings_sem_interacoes(ambiente):
    cliente, _ = ambiente

    ouvidas = cliente.get("/descoberta/mais-ouvidas")
    avaliadas = cliente.get("/descoberta/melhor-avaliadas")

    assert ouvidas.status_code == 200
    assert avaliadas.status_code == 200

    assert ouvidas.json() == []
    assert avaliadas.json() == []


# -----------------------------------------
# MAIS OUVIDAS
# -----------------------------------------


def test_mais_ouvidas_conta_escutas_repetidas(ambiente):
    cliente, motor = ambiente

    with Session(motor) as sessao:
        usuarios, obras = criar_catalogo(sessao)

        adicionar_escutas(sessao, usuarios[0], obras[0], 2)
        adicionar_escutas(sessao, usuarios[1], obras[0], 1)
        adicionar_escutas(sessao, usuarios[0], obras[1], 2)

        sessao.commit()

    resposta = cliente.get("/descoberta/mais-ouvidas")

    assert resposta.status_code == 200

    resultados = resposta.json()

    assert [item["titulo"] for item in resultados] == [
        "Disco 1",
        "Disco 2",
    ]

    assert [
        item["total_escutas"] for item in resultados
    ] == [3, 2]

    assert resultados[0]["artista"] == "Artista 1"
    assert resultados[0]["tipo"] == "Album"


def test_mais_ouvidas_empate_e_limite(ambiente):
    cliente, motor = ambiente

    with Session(motor) as sessao:
        usuarios, obras = criar_catalogo(sessao)

        adicionar_escutas(sessao, usuarios[0], obras[0], 2)
        adicionar_escutas(sessao, usuarios[0], obras[1], 2)

        sessao.commit()

    resposta = cliente.get(
        "/descoberta/mais-ouvidas",
        params={"limite": 1},
    )

    assert resposta.status_code == 200
    assert len(resposta.json()) == 1
    assert resposta.json()[0]["titulo"] == "Disco 1"


# -----------------------------------------
# MELHOR AVALIADAS
# -----------------------------------------


def test_melhor_avaliadas_calcula_medias(ambiente):
    cliente, motor = ambiente

    with Session(motor) as sessao:
        usuarios, obras = criar_catalogo(sessao)

        adicionar_avaliacao(
            sessao, usuarios[0], obras[0], 4.5
        )
        adicionar_avaliacao(
            sessao, usuarios[1], obras[0], 3.5
        )
        adicionar_avaliacao(
            sessao, usuarios[0], obras[1], 5.0
        )

        sessao.commit()

    resposta = cliente.get(
        "/descoberta/melhor-avaliadas"
    )

    assert resposta.status_code == 200

    resultados = resposta.json()

    assert [item["titulo"] for item in resultados] == [
        "Disco 2",
        "Disco 1",
    ]

    assert [item["media"] for item in resultados] == [
        5.0,
        4.0,
    ]

    assert [
        item["quantidade_avaliacoes"]
        for item in resultados
    ] == [1, 2]


def test_empate_de_media_prioriza_quantidade(ambiente):
    cliente, motor = ambiente

    with Session(motor) as sessao:
        usuarios, obras = criar_catalogo(sessao)

        adicionar_avaliacao(
            sessao, usuarios[0], obras[0], 4.0
        )

        for usuario in usuarios:
            adicionar_avaliacao(
                sessao, usuario, obras[1], 4.0
            )
            adicionar_avaliacao(
                sessao, usuario, obras[2], 4.0
            )

        sessao.commit()

    resposta = cliente.get(
        "/descoberta/melhor-avaliadas"
    )

    assert resposta.status_code == 200

    assert [
        item["titulo"] for item in resposta.json()
    ] == [
        "Disco 2",
        "Disco 3",
        "Disco 1",
    ]


# -----------------------------------------
# VALIDACAO DE LIMITES
# -----------------------------------------


@pytest.mark.parametrize(
    "rota",
    [
        "/descoberta/mais-ouvidas",
        "/descoberta/melhor-avaliadas",
    ],
)
def test_limites_invalidos(ambiente, rota):
    cliente, _ = ambiente

    for limite in [0, -1, 51, "abc"]:
        resposta = cliente.get(
            rota,
            params={"limite": limite},
        )

        assert resposta.status_code == 422

    resposta_valida = cliente.get(
        rota,
        params={"limite": 50},
    )

    assert resposta_valida.status_code == 200
