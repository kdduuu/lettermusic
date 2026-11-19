"""Contratos da comunidade: somente contribuicoes publicas."""
from datetime import datetime
from typing import Literal

from pydantic import BaseModel


class AtividadeBase(BaseModel):
    id: int
    username: str
    nome_exibicao: str
    criada_em: datetime


class AtividadeObra(AtividadeBase):
    id_musicbrainz: str
    titulo: str
    artista: str | None


class AtividadeReview(AtividadeObra):
    tipo: Literal["review"] = "review"
    texto: str


class AtividadeAvaliacao(AtividadeObra):
    tipo: Literal["avaliacao"] = "avaliacao"
    nota: float


class AtividadeLista(AtividadeBase):
    tipo: Literal["lista"] = "lista"
    titulo: str


class MembroAtivo(BaseModel):
    username: str
    nome_exibicao: str
    contribuicoes: int


class ObraEmAlta(BaseModel):
    id_musicbrainz: str
    titulo: str
    artista: str | None
    contribuicoes: int
    membros: int


class ComunidadePublica(BaseModel):
    janela_dias: int
    atividades: list[AtividadeReview | AtividadeAvaliacao | AtividadeLista]
    membros_ativos: list[MembroAtivo]
    em_alta: list[ObraEmAlta]