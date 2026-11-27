import os
from datetime import datetime, timedelta, timezone

import jwt
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt.exceptions import InvalidTokenError
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from backend.app.database import obter_sessao
from backend.app.models import Usuario
from backend.app.recuperacao_email import verificacao_obrigatoria
from backend.app.usuarios import protetor_senhas


ESQUEMA_BEARER = HTTPBearer(auto_error=False)
HASH_FICTICIO = protetor_senhas.hash("senha-ficticia")


def obter_chave():
    chave = os.getenv("JWT_SECRET")

    if not chave or len(chave) < 32:
        raise RuntimeError("Configure JWT_SECRET no arquivo .env")

    return chave


def erro_autenticacao():
    return HTTPException(
        status_code=401,
        detail="Credenciais invalidas.",
        headers={"WWW-Authenticate": "Bearer"}
    )


def autenticar_usuario(
    sessao: Session,
    identificador: str,
    senha: str
) -> Usuario:
    identificador = identificador.strip().lower()

    usuario = sessao.scalar(
        select(Usuario).where(
            or_(
                Usuario.username == identificador,
                Usuario.email == identificador
            )
        )
    )

    # Verifica um hash ficticio caso a conta nao exista.
    hash_senha = usuario.senha_hash if usuario else HASH_FICTICIO
    senha_correta = protetor_senhas.verify(senha, hash_senha)

    if usuario is None or not senha_correta:
        raise erro_autenticacao()

    return usuario


def criar_token(usuario_id: int, versao: int = 0) -> str:
    expiracao = datetime.now(timezone.utc) + timedelta(minutes=30)

    return jwt.encode(
        {"sub": str(usuario_id), "exp": expiracao, "ver": versao},
        obter_chave(),
        algorithm="HS256"
    )


def obter_usuario_atual(
    credenciais: HTTPAuthorizationCredentials | None = Depends(ESQUEMA_BEARER),
    sessao: Session = Depends(obter_sessao)
) -> Usuario:
    if credenciais is None:
        raise erro_autenticacao()

    try:
        dados = jwt.decode(
            credenciais.credentials,
            obter_chave(),
            algorithms=["HS256"],
            options={"require": ["sub", "exp", "ver"]}
        )

        sub = dados["sub"]
        if (
            not isinstance(sub, str)
            or not sub.isascii()
            or not sub.isdecimal()
            or len(sub) > 10
            or type(dados["exp"]) is not int
            or type(dados["ver"]) is not int
            or dados["ver"] < 0
        ):
            raise ValueError("Claims invalidas")

        usuario_id = int(sub)
        if not 1 <= usuario_id <= 2_147_483_647 or str(usuario_id) != sub:
            raise ValueError("Identificador de usuario invalido")

    except (InvalidTokenError, KeyError, ValueError, TypeError, OverflowError):
        raise erro_autenticacao() from None

    usuario = sessao.get(Usuario, usuario_id)

    if usuario is None or dados["ver"] != usuario.sessao_versao:
        raise erro_autenticacao()

    # A politica atual tambem vale para sessoes emitidas anteriormente.
    if verificacao_obrigatoria() and not usuario.email_confirmado:
        raise HTTPException(403, "Confirme seu e-mail antes de entrar.")

    return usuario