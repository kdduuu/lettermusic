from datetime import datetime, timedelta, timezone

import pytest

from fastapi import HTTPException
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event, select
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from backend.app import limites_cadastro, limites_login
from backend.app import recuperacao_email as rec
from backend.app.database import obter_sessao
from backend.app.limpeza_tokens import (
    contar_tokens,
    limpar_tokens,
)
from backend.app.main import app
from backend.app.models import (
    Base,
    ListaMusical,
    TokenConta,
    Usuario,
)


SENHA = "SenhaDeTeste#2026"


@pytest.fixture
def ambiente(monkeypatch):
    monkeypatch.setenv(
        "JWT_SECRET",
        "chave-ficticia-seguranca-f086c-2026"
    )
    monkeypatch.setenv(
        "EMAIL_REQUIRE_VERIFICATION", "false"
    )
    monkeypatch.setattr(
        rec, "email_configurado", lambda: False
    )

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
        app.dependency_overrides.pop(
            obter_sessao, None
        )
        motor.dispose()


def cadastrar(cliente, nome):
    return cliente.post("/usuarios", json={
        "username": nome,
        "nome_exibicao": f"Perfil {nome}",
        "email": f"{nome}@example.com",
        "senha": SENHA,
    })


def autenticar(cliente, nome):
    resposta = cliente.post("/auth/login", json={
        "identificador": nome,
        "senha": SENHA,
    })
    assert resposta.status_code == 200

    return {
        "Authorization": (
            f"Bearer {resposta.json()['access_token']}"
        )
    }


def test_cadastro_limita_tentativas_por_ip(
    ambiente, monkeypatch
):
    cliente, _ = ambiente

    monkeypatch.setattr(
        limites_cadastro, "LIMITE_ORIGEM", 2
    )

    assert cadastrar(
        cliente, "cadastro_um"
    ).status_code == 201

    assert cadastrar(
        cliente, "cadastro_dois"
    ).status_code == 201

    bloqueio = cadastrar(
        cliente, "cadastro_tres"
    )

    assert bloqueio.status_code == 429
    assert bloqueio.headers["Retry-After"] == "900"


def test_limite_login_compartilhado_entre_ips():
    for _ in range(limites_login.LIMITE_CONTA):
        limites_login.registrar_falha(
            "198.51.100.10", "usuario_alvo"
        )

    with pytest.raises(HTTPException) as erro:
        limites_login.verificar(
            "198.51.100.11", "USUARIO_ALVO"
        )

    assert erro.value.status_code == 429


def test_confirmacao_invalida_outros_links(ambiente):
    cliente, motor = ambiente

    assert cadastrar(
        cliente, "confirmacao_dupla"
    ).status_code == 201

    with Session(motor) as sessao:
        usuario = sessao.scalar(
            select(Usuario).where(
                Usuario.username == "confirmacao_dupla"
            )
        )
        primeiro = rec.emitir_token(
            sessao, usuario, "verificacao"
        )
        segundo = rec.emitir_token(
            sessao, usuario, "verificacao"
        )

    resposta = cliente.post(
        "/auth/email/confirmar",
        json={"token": primeiro},
    )
    assert resposta.status_code == 204

    reutilizacao = cliente.post(
        "/auth/email/confirmar",
        json={"token": segundo},
    )
    assert reutilizacao.status_code == 400


def test_limpeza_preserva_tokens_validos(ambiente):
    cliente, motor = ambiente

    assert cadastrar(
        cliente, "tokens_limpeza"
    ).status_code == 201

    agora = datetime.now(timezone.utc)

    with Session(motor) as sessao:
        usuario = sessao.scalar(
            select(Usuario).where(
                Usuario.username == "tokens_limpeza"
            )
        )

        casos = [
            ("expirado", agora - timedelta(hours=1), None),
            ("utilizado", agora + timedelta(hours=1), agora),
            ("valido", agora + timedelta(hours=1), None),
        ]

        for nome, expiracao, usado in casos:
            sessao.add(TokenConta(
                usuario_id=usuario.id,
                finalidade="senha",
                token_hash=rec.digest(nome),
                expira_em=expiracao,
                usado_em=usado,
            ))

        sessao.commit()

        assert contar_tokens(sessao, agora) == 2
        assert limpar_tokens(sessao, agora) == 2
        assert contar_tokens(sessao, agora) == 0

        restantes = sessao.scalars(
            select(TokenConta)
        ).all()

        assert len(restantes) == 1
        assert restantes[0].token_hash == rec.digest("valido")


def test_exclusao_de_conta_preserva_outras_contas(ambiente):
    cliente, motor = ambiente

    assert cadastrar(
        cliente, "exclusao_dono"
    ).status_code == 201
    assert cadastrar(
        cliente, "exclusao_outro"
    ).status_code == 201

    dono = autenticar(cliente, "exclusao_dono")
    outro = autenticar(cliente, "exclusao_outro")

    lista_dono = cliente.post(
        "/listas",
        headers=dono,
        json={"titulo": "Minha lista", "publica": True},
    )
    assert lista_dono.status_code == 201

    lista_outro = cliente.post(
        "/listas",
        headers=outro,
        json={"titulo": "Outra lista", "publica": True},
    )
    assert lista_outro.status_code == 201

    id_dono = lista_dono.json()["id"]
    id_outro = lista_outro.json()["id"]

    incorreta = cliente.request(
        "DELETE",
        "/auth/conta",
        headers=dono,
        json={"senha_atual": "senha-incorreta"},
    )
    assert incorreta.status_code == 400

    exclusao = cliente.request(
        "DELETE",
        "/auth/conta",
        headers=dono,
        json={"senha_atual": SENHA},
    )
    assert exclusao.status_code == 204

    assert cliente.get(
        "/auth/conta", headers=dono
    ).status_code == 401

    assert cliente.get(
        "/usuarios/exclusao_dono"
    ).status_code == 404

    assert cliente.get(
        f"/listas/{id_dono}"
    ).status_code == 404

    assert cliente.get(
        f"/listas/{id_outro}"
    ).status_code == 200

    with Session(motor) as sessao:
        assert sessao.scalar(
            select(Usuario).where(
                Usuario.username == "exclusao_dono"
            )
        ) is None

        assert sessao.scalar(
            select(ListaMusical).where(
                ListaMusical.id == id_dono
            )
        ) is None
