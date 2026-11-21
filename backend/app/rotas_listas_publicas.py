"""Listas publicas para descoberta social."""

from datetime import datetime

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from backend.app.database import obter_sessao
from backend.app.models import ItemLista, ListaMusical, Usuario


router = APIRouter(prefix="/listas", tags=["Listas Publicas"])


class ListaDescoberta(BaseModel):
    id: int
    titulo: str
    descricao: str | None
    username: str
    nome_exibicao: str
    total_itens: int
    criada_em: datetime


class PaginaListasPublicas(BaseModel):
    pagina: int
    por_pagina: int
    total: int
    tem_proxima: bool
    resultados: list[ListaDescoberta]


@router.get("/publicas", response_model=PaginaListasPublicas)
def explorar_listas_publicas(
    pagina: int = Query(default=1, ge=1, le=10000),
    por_pagina: int = Query(default=12, ge=1, le=30),
    sessao: Session = Depends(obter_sessao),
):
    # Contar apenas listas publicas.
    total = sessao.scalar(
        select(func.count(ListaMusical.id))
        .where(ListaMusical.publica.is_(True))
    ) or 0

    # Contagem correlacionada evita uma consulta por lista.
    itens = (
        select(func.count(ItemLista.id))
        .where(ItemLista.lista_id == ListaMusical.id)
        .correlate(ListaMusical)
        .scalar_subquery()
    )

    consulta = (
        select(
            ListaMusical,
            Usuario.username,
            Usuario.nome_exibicao,
            itens.label("total_itens"),
        )
        .join(Usuario, Usuario.id == ListaMusical.usuario_id)
        .where(ListaMusical.publica.is_(True))
        .order_by(
            ListaMusical.criada_em.desc(),
            ListaMusical.id.desc(),
        )
        .offset((pagina - 1) * por_pagina)
        .limit(por_pagina)
    )

    linhas = sessao.execute(consulta).all()

    resultados = [
        ListaDescoberta(
            id=lista.id,
            titulo=lista.titulo,
            descricao=lista.descricao,
            username=username,
            nome_exibicao=nome_exibicao,
            total_itens=total_itens,
            criada_em=lista.criada_em,
        )
        for lista, username, nome_exibicao, total_itens in linhas
    ]

    return PaginaListasPublicas(
        pagina=pagina,
        por_pagina=por_pagina,
        total=total,
        tem_proxima=pagina * por_pagina < total,
        resultados=resultados,
    )
