"""Limpeza de links usados ou expirados."""

from datetime import datetime, timezone

from sqlalchemy import delete, func, or_, select
from sqlalchemy.orm import Session

from backend.app.models import TokenConta


def condicao_limpeza(instante):
    return or_(
        TokenConta.expira_em <= instante,
        TokenConta.usado_em.is_not(None),
    )


def contar_tokens(sessao: Session, instante=None) -> int:
    instante = instante or datetime.now(timezone.utc)

    return sessao.scalar(
        select(func.count(TokenConta.id))
        .where(condicao_limpeza(instante))
    ) or 0


def limpar_tokens(sessao: Session, instante=None) -> int:
    instante = instante or datetime.now(timezone.utc)

    resultado = sessao.execute(
        delete(TokenConta).where(condicao_limpeza(instante))
    )

    sessao.commit()
    return resultado.rowcount or 0
