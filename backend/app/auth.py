
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

    # Verifica um hash fictício caso a conta não exista.
    hash_senha = usuario.senha_hash if usuario else HASH_FICTICIO
    senha_correta = protetor_senhas.verify(senha, hash_senha)

    if usuario is None or not senha_correta:
        raise erro_autenticacao()

    return usuario


def criar_token(usuario_id: int) -> str:
    expiracao = datetime.now(timezone.utc) + timedelta(minutes=30)

    return jwt.encode(
        {"sub": str(usuario_id), "exp": expiracao},
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
            algorithms=["HS256"]
        )
        usuario_id = int(dados["sub"])

    except (InvalidTokenError, KeyError, ValueError, TypeError):
        raise erro_autenticacao() from None

    usuario = sessao.get(Usuario, usuario_id)

    if usuario is None:
        raise erro_autenticacao()

    return usuario
