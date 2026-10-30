
from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from backend.app.interacoes import obter_ou_criar_obra
from backend.app.listas import (
    ListaNaoEncontrada,
    obter_lista_do_dono,
)
from backend.app.models import ItemLista, ListaMusical
from backend.app.schemas_interacoes import ObraInteracao


class ItemJaExisteNaLista(Exception):
    """A obra ja foi adicionada a esta lista."""


class ItemNaoEncontradoNaLista(Exception):
    """A obra nao pertence a esta lista."""


class PosicaoInvalida(Exception):
    """A posicao solicitada nao existe na lista."""


def _itens_ordenados(
    sessao: Session,
    lista_id: int,
) -> list[ItemLista]:
    """Busca os itens na ordem definida pelo usuario."""

    consulta = (
        select(ItemLista)
        .where(ItemLista.lista_id == lista_id)
        .order_by(
            ItemLista.posicao,
            ItemLista.id,
        )
    )

    return list(sessao.scalars(consulta))


# -----------------------------------------
# ADICIONAR
# -----------------------------------------


def adicionar_item_lista(
    sessao: Session,
    usuario_id: int,
    lista_id: int,
    dados: ObraInteracao,
) -> ItemLista:
    """Adiciona uma obra ao final da lista."""

    try:
        lista = obter_lista_do_dono(
            sessao,
            usuario_id,
            lista_id,
        )

        obra = obter_ou_criar_obra(sessao, dados)

        existente = sessao.scalar(
            select(ItemLista.id).where(
                ItemLista.lista_id == lista_id,
                ItemLista.obra_id == obra.id,
            )
        )

        if existente is not None:
            raise ItemJaExisteNaLista()

        ultima_posicao = sessao.scalar(
            select(func.max(ItemLista.posicao))
            .where(ItemLista.lista_id == lista_id)
        )

        proxima_posicao = (ultima_posicao or 0) + 1

        item = ItemLista(
            lista_id=lista_id,
            obra_id=obra.id,
            posicao=proxima_posicao,
        )

        sessao.add(item)

        lista.atualizada_em = datetime.now(timezone.utc)

        sessao.commit()
        sessao.refresh(item)

        return item

    except Exception:
        sessao.rollback()
        raise


# -----------------------------------------
# CONSULTAR
# -----------------------------------------


def listar_itens_lista(
    sessao: Session,
    lista_id: int,
    usuario_id: int | None = None,
) -> list[ItemLista]:
    """Consulta itens se a lista for publica ou do usuario."""

    lista = sessao.get(ListaMusical, lista_id)

    if lista is None:
        raise ListaNaoEncontrada()

    if not lista.publica and lista.usuario_id != usuario_id:
        raise ListaNaoEncontrada()

    return _itens_ordenados(sessao, lista_id)


# -----------------------------------------
# REMOVER
# -----------------------------------------


def remover_item_lista(
    sessao: Session,
    usuario_id: int,
    lista_id: int,
    obra_id: int,
) -> None:
    """Remove uma obra e reorganiza as posicoes."""

    try:
        lista = obter_lista_do_dono(
            sessao,
            usuario_id,
            lista_id,
        )

        itens = _itens_ordenados(sessao, lista_id)

        item_remover = next(
            (
                item for item in itens
                if item.obra_id == obra_id
            ),
            None,
        )

        if item_remover is None:
            raise ItemNaoEncontradoNaLista()

        sessao.delete(item_remover)

        restantes = [
            item for item in itens
            if item.id != item_remover.id
        ]

        for posicao, item in enumerate(restantes, start=1):
            item.posicao = posicao

        lista.atualizada_em = datetime.now(timezone.utc)

        sessao.commit()

    except Exception:
        sessao.rollback()
        raise


# -----------------------------------------
# REORDENAR
# -----------------------------------------


def mover_item_lista(
    sessao: Session,
    usuario_id: int,
    lista_id: int,
    obra_id: int,
    nova_posicao: int,
) -> ItemLista:
    """Move um album e reorganiza os demais."""

    try:
        lista = obter_lista_do_dono(
            sessao,
            usuario_id,
            lista_id,
        )

        itens = _itens_ordenados(sessao, lista_id)

        item_mover = next(
            (
                item for item in itens
                if item.obra_id == obra_id
            ),
            None,
        )

        if item_mover is None:
            raise ItemNaoEncontradoNaLista()

        if not 1 <= nova_posicao <= len(itens):
            raise PosicaoInvalida()

        itens.remove(item_mover)

        itens.insert(nova_posicao - 1, item_mover)

        for posicao, item in enumerate(itens, start=1):
            item.posicao = posicao

        lista.atualizada_em = datetime.now(timezone.utc)

        sessao.commit()
        sessao.refresh(item_mover)

        return item_mover

    except Exception:
        sessao.rollback()
        raise
