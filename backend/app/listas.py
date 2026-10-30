
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.models import ListaMusical


class ListaNaoEncontrada(Exception):
    """Lista inexistente ou nao pertencente ao usuario."""


# -----------------------------------------
# CRIACAO
# -----------------------------------------


def criar_lista(
    sessao: Session,
    usuario_id: int,
    titulo: str,
    descricao: str | None = None,
    publica: bool = True,
) -> ListaMusical:
    """Cria uma lista musical para o usuario."""

    try:
        lista = ListaMusical(
            usuario_id=usuario_id,
            titulo=titulo,
            descricao=descricao,
            publica=publica,
        )

        sessao.add(lista)
        sessao.commit()
        sessao.refresh(lista)

        return lista

    except Exception:
        sessao.rollback()
        raise


# -----------------------------------------
# CONSULTAS
# -----------------------------------------


def listar_minhas_listas(
    sessao: Session,
    usuario_id: int,
) -> list[ListaMusical]:
    """Consulta as listas publicas e privadas do usuario."""

    consulta = (
        select(ListaMusical)
        .where(ListaMusical.usuario_id == usuario_id)
        .order_by(
            ListaMusical.criada_em.desc(),
            ListaMusical.id.desc(),
        )
        .limit(50)
    )

    return list(sessao.scalars(consulta))


def consultar_lista_publica(
    sessao: Session,
    lista_id: int,
) -> ListaMusical | None:
    """Consulta uma lista somente se ela for publica."""

    consulta = select(ListaMusical).where(
        ListaMusical.id == lista_id,
        ListaMusical.publica.is_(True),
    )

    return sessao.scalar(consulta)


def obter_lista_do_dono(
    sessao: Session,
    usuario_id: int,
    lista_id: int,
) -> ListaMusical:
    """Localiza uma lista pertencente ao usuario."""

    consulta = select(ListaMusical).where(
        ListaMusical.id == lista_id,
        ListaMusical.usuario_id == usuario_id,
    )

    lista = sessao.scalar(consulta)

    if lista is None:
        raise ListaNaoEncontrada()

    return lista


# -----------------------------------------
# EDICAO
# -----------------------------------------


def editar_lista(
    sessao: Session,
    usuario_id: int,
    lista_id: int,
    titulo: str,
    descricao: str | None,
    publica: bool,
) -> ListaMusical:
    """Atualiza os dados de uma lista do usuario."""

    try:
        lista = obter_lista_do_dono(
            sessao,
            usuario_id,
            lista_id,
        )

        lista.titulo = titulo
        lista.descricao = descricao
        lista.publica = publica
        lista.atualizada_em = datetime.now(timezone.utc)

        sessao.commit()
        sessao.refresh(lista)

        return lista

    except Exception:
        sessao.rollback()
        raise


# -----------------------------------------
# EXCLUSAO
# -----------------------------------------


def excluir_lista(
    sessao: Session,
    usuario_id: int,
    lista_id: int,
) -> None:
    """Exclui uma lista pertencente ao usuario."""

    try:
        lista = obter_lista_do_dono(
            sessao,
            usuario_id,
            lista_id,
        )

        sessao.delete(lista)
        sessao.commit()

    except Exception:
        sessao.rollback()
        raise
