"""Tokens de uso unico e mensagens de recuperacao/verificacao."""

import hashlib
import logging
import os
import re
import secrets
import smtplib
import ssl

from collections import deque
from datetime import datetime, timedelta, timezone
from email.message import EmailMessage
from threading import Lock
from time import monotonic
from urllib.parse import urlsplit

from fastapi import HTTPException
from sqlalchemy import update
from sqlalchemy.orm import Session

from backend.app.models import TokenConta, Usuario
from backend.app.usuarios import protetor_senhas


LOGGER = logging.getLogger(__name__)

JANELA = 900.0
LIMITE_EMAIL = 3
LIMITE_IP = 15

_lock = Lock()
_eventos = {}
_agora_limite = monotonic


def agora_utc():
    return datetime.now(timezone.utc)


def digest(valor):
    return hashlib.sha256(valor.encode("utf-8")).hexdigest()


def url_publica():
    """URL fixa configurada pelo servidor, nunca pelo header Host."""
    base = os.getenv("EMAIL_BASE_URL", "").rstrip("/")
    url = urlsplit(base)

    local = (
        url.scheme == "http"
        and url.hostname in {"localhost", "127.0.0.1"}
    )

    segura = url.scheme == "https"

    if (
        not (local or segura)
        or not url.netloc
        or url.username
        or url.password
        or url.path
        or url.query
        or url.fragment
    ):
        return None

    return base


def email_configurado():
    return bool(
        os.getenv("SMTP_HOST")
        and os.getenv("SMTP_FROM")
        and url_publica()
    )


def verificacao_obrigatoria():
    return os.getenv(
        "EMAIL_REQUIRE_VERIFICATION", "false"
    ).lower() == "true"


def limitar_solicitacao(ip, identificador):
    """Limita envios, independentemente de a conta existir."""
    chaves = [
        ("email:" + digest(identificador.strip().casefold()), LIMITE_EMAIL),
        ("ip:" + digest(ip), LIMITE_IP),
    ]

    agora = _agora_limite()

    with _lock:
        for chave, limite in chaves:
            registros = _eventos.get(chave, deque())

            while registros and registros[0] <= agora - JANELA:
                registros.popleft()

            if len(registros) >= limite:
                raise HTTPException(
                    status_code=429,
                    detail="Aguarde antes de solicitar outro e-mail.",
                    headers={"Retry-After": "900"},
                )

        for chave, _ in chaves:
            registros = _eventos.setdefault(chave, deque())
            registros.append(agora)

        if len(_eventos) > 4096:
            for chave in list(_eventos)[:1024]:
                _eventos.pop(chave, None)


def emitir_token(sessao: Session, usuario: Usuario, finalidade: str):
    if finalidade not in {"senha", "verificacao"}:
        raise ValueError("Finalidade de token invalida")

    segredo = secrets.token_urlsafe(32)

    duracao = (
        timedelta(minutes=30)
        if finalidade == "senha"
        else timedelta(hours=24)
    )

    sessao.add(
        TokenConta(
            usuario_id=usuario.id,
            finalidade=finalidade,
            token_hash=digest(segredo),
            expira_em=agora_utc() + duracao,
        )
    )

    # Nenhum token em texto puro fica armazenado no banco.
    sessao.commit()

    return segredo


def consumir_token(
    sessao: Session,
    segredo: str,
    finalidade: str,
):
    if not re.fullmatch(r"[A-Za-z0-9_-]{43}", segredo):
        return None

    instante = agora_utc()

    # UPDATE atomico: apenas a primeira requisicao consome o token.
    consulta = (
        update(TokenConta)
        .where(
            TokenConta.token_hash == digest(segredo),
            TokenConta.finalidade == finalidade,
            TokenConta.usado_em.is_(None),
            TokenConta.expira_em > instante,
        )
        .values(usado_em=instante)
        .returning(TokenConta.usuario_id)
    )

    usuario_id = sessao.execute(consulta).scalar_one_or_none()

    if usuario_id is None:
        sessao.rollback()
        return None

    return sessao.get(Usuario, usuario_id)


def redefinir_senha(sessao: Session, segredo: str, nova_senha: str):
    usuario = consumir_token(sessao, segredo, "senha")

    if usuario is None:
        raise HTTPException(
            400, "Link invalido, expirado ou ja utilizado."
        )

    usuario.senha_hash = protetor_senhas.hash(nova_senha)
    usuario.sessao_versao += 1

    # Invalida tambem os outros links de recuperacao pendentes.
    sessao.execute(
        update(TokenConta)
        .where(
            TokenConta.usuario_id == usuario.id,
            TokenConta.finalidade == "senha",
            TokenConta.usado_em.is_(None),
        )
        .values(usado_em=agora_utc())
    )

    sessao.commit()


def confirmar_email(sessao: Session, segredo: str):
    usuario = consumir_token(sessao, segredo, "verificacao")

    if usuario is None:
        raise HTTPException(
            400, "Link invalido, expirado ou ja utilizado."
        )

    usuario.email_confirmado = True
    sessao.commit()


def enviar_mensagem(destinatario, finalidade, segredo):
    """Envio SMTP. Erros nao revelam tokens nem credenciais."""
    base = url_publica()

    if not base or not email_configurado():
        LOGGER.error("Envio de email nao configurado.")
        return

    if finalidade == "senha":
        endereco = f"{base}/redefinir-senha?token={segredo}"
        titulo = "Lettermusic | Redefinir senha"
        texto = (
            "Recebemos uma solicitacao de recuperacao de senha.\n\n"
            f"Abra o link: {endereco}\n\n"
            "Este link expira em 30 minutos e pode ser usado uma vez.\n"
            "Se voce nao solicitou, ignore esta mensagem."
        )
    else:
        endereco = f"{base}/confirmar-email?token={segredo}"
        titulo = "Lettermusic | Confirmar e-mail"
        texto = (
            "Confirme seu e-mail no Lettermusic.\n\n"
            f"Abra o link: {endereco}\n\n"
            "Este link expira em 24 horas e pode ser usado uma vez.\n"
            "Se voce nao criou esta conta, ignore a mensagem."
        )

    mensagem = EmailMessage()
    mensagem["From"] = os.environ["SMTP_FROM"]
    mensagem["To"] = destinatario
    mensagem["Subject"] = titulo
    mensagem.set_content(texto)

    host = os.environ["SMTP_HOST"]
    porta = int(os.getenv("SMTP_PORT", "587"))
    usuario = os.getenv("SMTP_USER")
    senha = os.getenv("SMTP_PASSWORD")

    try:
        if os.getenv("SMTP_SSL", "false").lower() == "true":
            conexao = smtplib.SMTP_SSL(
                host, porta, timeout=10,
                context=ssl.create_default_context(),
            )
        else:
            conexao = smtplib.SMTP(host, porta, timeout=10)

        with conexao as smtp:
            if os.getenv("SMTP_SSL", "false").lower() != "true":
                smtp.starttls(context=ssl.create_default_context())

            if usuario and senha:
                smtp.login(usuario, senha)

            smtp.send_message(mensagem)

    except (OSError, smtplib.SMTPException, ValueError):
        LOGGER.error(
            "Falha no envio de e-mail do Lettermusic."
        )
