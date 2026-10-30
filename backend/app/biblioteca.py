
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.interacoes import obter_ou_criar_obra
from backend.app.models import Favorito, QueroOuvir
from backend.app.schemas_interacoes import ObraInteracao


class ItemJaExiste(Exception):
    """A obra ja pertence a esta colecao."""


class ItemNaoEncontrado(Exception):
    """A obra nao pertence a esta colecao."""


def _adicionar(
    sessao: Session,
    usuario_id: int,
    dados: ObraInteracao,
    modelo,
):
    """Adiciona uma obra a uma colecao pessoal."""

    try:
        obra = obter_ou_criar_obra(sessao, dados)

        existente = sessao.scalar(
            select(modelo.id).where(
                modelo.usuario_id == usuario_id,
                modelo.obra_id == obra.id,
            )
        )

        if existente is not None:
            raise ItemJaExiste()

        registro = modelo(
            usuario_id=usuario_id,
            obra_id=obra.id,
        )

        sessao.add(registro)
        sessao.commit()
        sessao.refresh(registro)

        return registro

    except Exception:
        sessao.rollback()
        raise


def _listar(
    sessao: Session,
    usuario_id: int,
    modelo,
):
    """Lista as ultimas 50 obras de uma colecao."""

    consulta = (
        select(modelo)
        .where(modelo.usuario_id == usuario_id)
        .order_by(
            modelo.adicionado_em.desc(),
            modelo.id.desc(),
        )
        .limit(50)
    )

    return list(sessao.scalars(consulta))


def _remover(
    sessao: Session,
    usuario_id: int,
    obra_id: int,
    modelo,
) -> None:
    """Remove uma obra da colecao pessoal."""

    try:
        registro = sessao.scalar(
            select(modelo).where(
                modelo.usuario_id == usuario_id,
                modelo.obra_id == obra_id,
            )
        )

        if registro is None:
            raise ItemNaoEncontrado()

        sessao.delete(registro)
        sessao.commit()

    except Exception:
        sessao.rollback()
        raise


# -----------------------------------------
# FAVORITOS
# -----------------------------------------


def adicionar_favorito(
    sessao: Session,
    usuario_id: int,
    dados: ObraInteracao,
) -> Favorito:
    return _adicionar(
        sessao, usuario_id, dados, Favorito
    )


def listar_favoritos(
    sessao: Session,
    usuario_id: int,
) -> list[Favorito]:
    return _listar(sessao, usuario_id, Favorito)


def remover_favorito(
    sessao: Session,
    usuario_id: int,
    obra_id: int,
) -> None:
    _remover(sessao, usuario_id, obra_id, Favorito)


# -----------------------------------------
# QUERO OUVIR
# -----------------------------------------


def adicionar_quero_ouvir(
    sessao: Session,
    usuario_id: int,
    dados: ObraInteracao,
) -> QueroOuvir:
    return _adicionar(
        sessao, usuario_id, dados, QueroOuvir
    )


def listar_quero_ouvir(
    sessao: Session,
    usuario_id: int,
) -> list[QueroOuvir]:
    return _listar(sessao, usuario_id, QueroOuvir)


def remover_quero_ouvir(
    sessao: Session,
    usuario_id: int,
    obra_id: int,
) -> None:
    _remover(sessao, usuario_id, obra_id, QueroOuvir)
