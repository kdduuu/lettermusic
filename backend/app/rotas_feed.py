"""Rotas de leitura social publica, separadas das mutacoes."""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from backend.app.comunidade import consultar_comunidade
from backend.app.database import obter_sessao
from backend.app.feed_reviews import listar_feed_reviews
from backend.app.schemas_comunidade import ComunidadePublica
from backend.app.schemas_feed import PaginaReviews

router = APIRouter(prefix="/social", tags=["Feed Social"])


@router.get("/reviews", response_model=PaginaReviews)
def consultar_feed_reviews(
    pagina: int = Query(default=1, ge=1, le=10000),
    por_pagina: int = Query(default=12, ge=1, le=50),
    sessao: Session = Depends(obter_sessao),
):
    return listar_feed_reviews(sessao, pagina, por_pagina)


@router.get("/comunidade", response_model=ComunidadePublica)
def obter_comunidade(sessao: Session = Depends(obter_sessao)):
    return consultar_comunidade(sessao)