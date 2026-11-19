"""Contrato explicito do feed publico de reviews."""
from datetime import datetime

from pydantic import BaseModel


class ReviewFeed(BaseModel):
    id: int
    username: str
    nome_exibicao: str
    id_musicbrainz: str
    titulo: str
    artista: str | None
    texto: str
    nota: float | None
    criada_em: datetime
    atualizada_em: datetime | None


class PaginaReviews(BaseModel):
    pagina: int
    por_pagina: int
    tem_proxima: bool
    resultados: list[ReviewFeed]