
from datetime import datetime, timedelta, timezone

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
    ListaMusical,
    Obra,
    Review,
    Usuario,
)


# -----------------------------------------
# AMBIENTE DE TESTES
# -----------------------------------------


@pytest.fixture
def ambiente():
    """Cria uma API com banco temporario e isolado."""

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


# -----------------------------------------
# DADOS FICTICIOS
# -----------------------------------------


def criar_usuario(sessao, username="radiohead_fan"):
    usuario = Usuario(
        username=username,
        nome_exibicao="Usuario de teste",
        email=f"{username}@example.com",
        senha_hash="hash-ficticio-para-testes",
        bio="Gosto de descobrir musica.",
    )

    sessao.add(usuario)
    sessao.flush()

    return usuario


def criar_obra(sessao, numero):
    obra = Obra(
        id_musicbrainz=(
            f"00000000-0000-0000-0000-{numero:012d}"
        ),
        titulo=f"Disco {numero}",
        artista=f"Artista {numero}",
        tipo="Album",
    )

    sessao.add(obra)
    sessao.flush()

    return obra


# -----------------------------------------
# CONSULTA PUBLICA
# -----------------------------------------


def test_perfil_publico_sem_login_e_sem_dados_sensiveis(
    ambiente,
):
    cliente, motor = ambiente

    with Session(motor) as sessao:
        criar_usuario(sessao)
        sessao.commit()

    resposta = cliente.get(
        "/usuarios/RADIOHEAD_FAN/social"
    )

    assert resposta.status_code == 200

    dados = resposta.json()

    assert dados["username"] == "radiohead_fan"
    assert dados["nome_exibicao"] == "Usuario de teste"
    assert dados["bio"] == "Gosto de descobrir musica."

    assert dados["estatisticas"] == {
        "avaliacoes": 0,
        "reviews": 0,
        "listas_publicas": 0,
    }

    assert dados["reviews_recentes"] == []
    assert dados["listas_publicas"] == []

    assert "email" not in dados
    assert "senha_hash" not in dados
    assert "access_token" not in dados
    assert "escutas" not in dados


# -----------------------------------------
# USUARIO INEXISTENTE
# -----------------------------------------


def test_usuario_inexistente_retorna_404(ambiente):
    cliente, _ = ambiente

    resposta = cliente.get(
        "/usuarios/usuario_inexistente/social"
    )

    assert resposta.status_code == 404
    assert resposta.json()["detail"] == (
        "Usuario nao encontrado."
    )


# -----------------------------------------
# ESTATISTICAS E PRIVACIDADE
# -----------------------------------------


def test_estatisticas_respeitam_usuario_e_privacidade(
    ambiente,
):
    cliente, motor = ambiente

    with Session(motor) as sessao:
        usuario = criar_usuario(sessao)
        outro = criar_usuario(sessao, "outro_usuario")

        obra_1 = criar_obra(sessao, 1)
        obra_2 = criar_obra(sessao, 2)

        sessao.add_all(
            [
                Avaliacao(
                    usuario_id=usuario.id,
                    obra_id=obra_1.id,
                    nota_passos=10,
                ),
                Avaliacao(
                    usuario_id=outro.id,
                    obra_id=obra_2.id,
                    nota_passos=8,
                ),
                Review(
                    usuario_id=usuario.id,
                    obra_id=obra_1.id,
                    texto="Minha review publica.",
                ),
                Review(
                    usuario_id=outro.id,
                    obra_id=obra_2.id,
                    texto="Review de outro usuario.",
                ),
                ListaMusical(
                    usuario_id=usuario.id,
                    titulo="Minha lista publica",
                    publica=True,
                ),
                ListaMusical(
                    usuario_id=usuario.id,
                    titulo="Minha lista secreta",
                    publica=False,
                ),
                ListaMusical(
                    usuario_id=outro.id,
                    titulo="Lista de outro usuario",
                    publica=True,
                ),
                Escuta(
                    usuario_id=usuario.id,
                    obra_id=obra_1.id,
                ),
            ]
        )

        sessao.commit()

    resposta = cliente.get(
        "/usuarios/radiohead_fan/social"
    )

    assert resposta.status_code == 200

    dados = resposta.json()

    assert dados["estatisticas"] == {
        "avaliacoes": 1,
        "reviews": 1,
        "listas_publicas": 1,
    }

    assert len(dados["reviews_recentes"]) == 1
    assert dados["reviews_recentes"][0]["titulo"] == (
        "Disco 1"
    )
    assert dados["reviews_recentes"][0]["texto"] == (
        "Minha review publica."
    )

    assert len(dados["listas_publicas"]) == 1
    assert dados["listas_publicas"][0]["titulo"] == (
        "Minha lista publica"
    )

    assert "Minha lista secreta" not in str(dados)
    assert "Lista de outro usuario" not in str(dados)
    assert "Review de outro usuario" not in str(dados)


# -----------------------------------------
# REVIEWS RECENTES
# -----------------------------------------


def test_reviews_recentes_ordenadas_e_limitadas(ambiente):
    cliente, motor = ambiente

    instante = datetime(
        2026, 10, 1, tzinfo=timezone.utc
    )

    with Session(motor) as sessao:
        usuario = criar_usuario(sessao)

        for numero in range(1, 8):
            obra = criar_obra(sessao, numero)

            sessao.add(
                Review(
                    usuario_id=usuario.id,
                    obra_id=obra.id,
                    texto=f"Review do Disco {numero}.",
                    criada_em=(
                        instante + timedelta(days=numero)
                    ),
                )
            )

        sessao.commit()

    resposta = cliente.get(
        "/usuarios/radiohead_fan/social"
    )

    assert resposta.status_code == 200

    dados = resposta.json()

    assert dados["estatisticas"]["reviews"] == 7

    assert len(dados["reviews_recentes"]) == 5

    assert [
        review["titulo"]
        for review in dados["reviews_recentes"]
    ] == [
        "Disco 7",
        "Disco 6",
        "Disco 5",
        "Disco 4",
        "Disco 3",
    ]

    assert dados["reviews_recentes"][0]["artista"] == (
        "Artista 7"
    )


# -----------------------------------------
# LISTAS PUBLICAS
# -----------------------------------------


def test_listas_publicas_ordenadas_e_limitadas(ambiente):
    cliente, motor = ambiente

    instante = datetime(
        2026, 10, 1, tzinfo=timezone.utc
    )

    with Session(motor) as sessao:
        usuario = criar_usuario(sessao)

        for numero in range(1, 8):
            sessao.add(
                ListaMusical(
                    usuario_id=usuario.id,
                    titulo=f"Lista {numero}",
                    publica=True,
                    criada_em=(
                        instante + timedelta(days=numero)
                    ),
                )
            )

        sessao.add(
            ListaMusical(
                usuario_id=usuario.id,
                titulo="Lista privada",
                publica=False,
                criada_em=instante + timedelta(days=30),
            )
        )

        sessao.commit()

    resposta = cliente.get(
        "/usuarios/radiohead_fan/social"
    )

    assert resposta.status_code == 200

    dados = resposta.json()

    assert dados["estatisticas"]["listas_publicas"] == 7

    assert [
        lista["titulo"]
        for lista in dados["listas_publicas"]
    ] == [
        "Lista 7",
        "Lista 6",
        "Lista 5",
        "Lista 4",
        "Lista 3",
    ]

    assert "Lista privada" not in str(dados)


# -----------------------------------------
# VALIDACAO DO USERNAME
# -----------------------------------------


@pytest.mark.parametrize(
    "username",
    [
        "ab",
        "usuario-invalido",
    ],
)
def test_username_invalido_retorna_422(
    ambiente,
    username,
):
    cliente, _ = ambiente

    resposta = cliente.get(
        f"/usuarios/{username}/social"
    )

    assert resposta.status_code == 422
