from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from backend.app import recuperacao_email as rec
from backend.app.database import obter_sessao
from backend.app.main import app
from backend.app.models import Base, TokenConta


@pytest.fixture
def ambiente(monkeypatch):
    monkeypatch.setenv(
        "JWT_SECRET",
        "chave-ficticia-recuperacao-lettermusic-2026"
    )
    monkeypatch.setenv("SMTP_HOST", "smtp.teste.local")
    monkeypatch.setenv("SMTP_FROM", "teste@example.com")
    monkeypatch.setenv(
        "EMAIL_BASE_URL", "http://localhost:3000"
    )
    monkeypatch.setenv(
        "EMAIL_REQUIRE_VERIFICATION", "false"
    )
    monkeypatch.setattr(rec, "_eventos", {})

    mensagens = []

    def simular_envio(destinatario, finalidade, token):
        mensagens.append((destinatario, finalidade, token))

    monkeypatch.setattr(
        rec, "enviar_mensagem", simular_envio
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
            resposta = cliente.post("/usuarios", json={
                "username": "recuperacao",
                "nome_exibicao": "Conta Teste",
                "email": "recuperacao@example.com",
                "senha": "SenhaOriginal#2026",
            })
            assert resposta.status_code == 201
            yield cliente, mensagens, motor

    finally:
        app.dependency_overrides.pop(obter_sessao, None)
        motor.dispose()


def login(cliente, senha="SenhaOriginal#2026"):
    return cliente.post("/auth/login", json={
        "identificador": "recuperacao",
        "senha": senha,
    })


def token_login(cliente):
    resposta = login(cliente)
    assert resposta.status_code == 200
    return resposta.json()["access_token"]


def cabecalho(token):
    return {"Authorization": f"Bearer {token}"}


def solicitar(cliente, email="recuperacao@example.com"):
    return cliente.post(
        "/auth/senha/solicitar",
        json={"email": email},
    )


def test_cadastro_emite_verificacao_e_uso_unico(ambiente):
    cliente, mensagens, _ = ambiente

    assert len(mensagens) == 1
    assert mensagens[0][1] == "verificacao"

    jwt = token_login(cliente)

    conta = cliente.get(
        "/auth/conta", headers=cabecalho(jwt)
    )

    assert conta.status_code == 200
    assert conta.json()["email_confirmado"] is False

    segredo = mensagens[0][2]

    resposta = cliente.post(
        "/auth/email/confirmar",
        json={"token": segredo},
    )
    assert resposta.status_code == 204

    assert cliente.get(
        "/auth/conta", headers=cabecalho(jwt)
    ).json()["email_confirmado"] is True

    reutilizado = cliente.post(
        "/auth/email/confirmar",
        json={"token": segredo},
    )
    assert reutilizado.status_code == 400


def test_recuperacao_senha_revoga_sessoes(ambiente):
    cliente, mensagens, _ = ambiente
    antigo = token_login(cliente)

    resposta = solicitar(cliente)
    assert resposta.status_code == 200

    segredo = mensagens[-1][2]
    assert mensagens[-1][1] == "senha"

    troca = cliente.post(
        "/auth/senha/redefinir",
        json={
            "token": segredo,
            "senha_nova": "NovaSenhaForte#2026",
        },
    )
    assert troca.status_code == 204

    assert cliente.get(
        "/auth/me", headers=cabecalho(antigo)
    ).status_code == 401

    assert login(cliente).status_code == 401

    assert login(
        cliente, "NovaSenhaForte#2026"
    ).status_code == 200

    assert cliente.post(
        "/auth/senha/redefinir",
        json={
            "token": segredo,
            "senha_nova": "OutraSenhaForte#2026",
        },
    ).status_code == 400


def test_resposta_nao_revela_conta(ambiente):
    cliente, mensagens, _ = ambiente

    existente = solicitar(cliente)
    quantidade = len(mensagens)

    inexistente = solicitar(
        cliente, "nao-existe@example.com"
    )

    assert existente.status_code == 200
    assert inexistente.status_code == 200
    assert existente.json() == inexistente.json()
    assert len(mensagens) == quantidade


def test_token_expirado_nao_funciona(ambiente):
    cliente, mensagens, motor = ambiente

    assert solicitar(cliente).status_code == 200
    segredo = mensagens[-1][2]

    with Session(motor) as sessao:
        registro = sessao.scalar(
            select(TokenConta).where(
                TokenConta.token_hash == rec.digest(segredo)
            )
        )
        assert registro is not None
        registro.expira_em = (
            datetime.now(timezone.utc)
            - timedelta(seconds=1)
        )
        sessao.commit()

    resposta = cliente.post(
        "/auth/senha/redefinir",
        json={
            "token": segredo,
            "senha_nova": "SenhaAtualizada#2026",
        },
    )

    assert resposta.status_code == 400


def test_limite_de_solicitacoes(ambiente):
    cliente, _, _ = ambiente

    for _ in range(rec.LIMITE_EMAIL):
        assert solicitar(cliente).status_code == 200

    bloqueada = solicitar(cliente)
    assert bloqueada.status_code == 429
    assert bloqueada.headers["Retry-After"] == "900"


def test_verificacao_obrigatoria_quando_ativada(
    ambiente, monkeypatch
):
    cliente, mensagens, _ = ambiente

    monkeypatch.setenv(
        "EMAIL_REQUIRE_VERIFICATION", "true"
    )

    assert login(cliente).status_code == 403

    assert cliente.post(
        "/auth/email/confirmar",
        json={"token": mensagens[0][2]},
    ).status_code == 204

    assert login(cliente).status_code == 200


def test_reenviar_confirmacao_sem_login(ambiente, monkeypatch):
    cliente, mensagens, _ = ambiente

    monkeypatch.setenv(
        "EMAIL_REQUIRE_VERIFICATION", "true"
    )

    assert login(cliente).status_code == 403

    resposta = cliente.post(
        "/auth/email/solicitar",
        json={"email": "recuperacao@example.com"},
    )

    assert resposta.status_code == 200
    assert mensagens[-1][1] == "verificacao"

    inexistente = cliente.post(
        "/auth/email/solicitar",
        json={"email": "ninguem@example.com"},
    )

    assert inexistente.status_code == 200
    assert inexistente.json() == resposta.json()

    assert cliente.post(
        "/auth/email/confirmar",
        json={"token": mensagens[-1][2]},
    ).status_code == 204

    assert login(cliente).status_code == 200


def test_redefinicao_invalida_outros_links(ambiente):
    cliente, mensagens, _ = ambiente

    assert solicitar(cliente).status_code == 200
    primeiro = mensagens[-1][2]

    assert solicitar(cliente).status_code == 200
    segundo = mensagens[-1][2]

    assert cliente.post(
        "/auth/senha/redefinir",
        json={
            "token": primeiro,
            "senha_nova": "OutraSenhaNova#2026",
        },
    ).status_code == 204

    assert cliente.post(
        "/auth/senha/redefinir",
        json={
            "token": segundo,
            "senha_nova": "MaisUmaSenha#2026",
        },
    ).status_code == 400


def test_envio_indisponivel_sem_smtp(ambiente, monkeypatch):
    cliente, _, _ = ambiente
    monkeypatch.delenv("SMTP_HOST", raising=False)

    resposta = solicitar(cliente)
    assert resposta.status_code == 503


def test_cadastro_obrigatorio_sem_smtp_nao_cria_conta(ambiente, monkeypatch):
    from backend.app.models import Usuario

    cliente, mensagens, motor = ambiente
    monkeypatch.setenv("EMAIL_REQUIRE_VERIFICATION", "true")
    monkeypatch.delenv("SMTP_HOST", raising=False)
    quantidade = len(mensagens)
    resposta = cliente.post("/usuarios", json={
        "username": "sem_smtp",
        "nome_exibicao": "Sem SMTP",
        "email": "sem-smtp@example.com",
        "senha": "SenhaOriginal#2026",
    })
    assert resposta.status_code == 503
    assert len(mensagens) == quantidade
    with Session(motor) as sessao:
        assert sessao.scalar(select(Usuario).where(Usuario.username == "sem_smtp")) is None
