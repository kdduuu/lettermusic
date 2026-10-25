
from pwdlib import PasswordHash
from sqlalchemy import or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from backend.app.models import Usuario
from backend.app.schemas import UsuarioCriar


protetor_senhas = PasswordHash.recommended()


class UsuarioJaExiste(Exception):
    pass


def cadastrar_usuario(
    sessao: Session,
    dados: UsuarioCriar
) -> Usuario:
    username = dados.username.lower()
    email = str(dados.email).lower()

    existente = sessao.scalar(
        select(Usuario.id).where(
            or_(
                Usuario.username == username,
                Usuario.email == email
            )
        )
    )

    if existente is not None:
        raise UsuarioJaExiste()

    usuario = Usuario(
        username=username,
        nome_exibicao=dados.nome_exibicao,
        email=email,
        senha_hash=protetor_senhas.hash(dados.senha)
    )

    sessao.add(usuario)

    try:
        sessao.commit()
    except IntegrityError as erro:
        sessao.rollback()
        raise UsuarioJaExiste() from erro

    sessao.refresh(usuario)
    return usuario


def buscar_usuario_por_username(
    sessao: Session,
    username: str
) -> Usuario | None:
    consulta = select(Usuario).where(
        Usuario.username == username.lower()
    )

    return sessao.scalar(consulta)
