"""Contratos de leitura da camada social, sem persistencia por visualizacao."""
from datetime import datetime
from pydantic import BaseModel, Field


class ReviewPublicaResumo(BaseModel):
    username: str
    nome_exibicao: str
    texto: str
    criada_em: datetime


class ResumoSocialAlbum(BaseModel):
    obra_id: int | None = None
    media_avaliacoes: float | None = None
    quantidade_avaliacoes: int = 0
    reviews: list[ReviewPublicaResumo] = Field(default_factory=list)


class MeuEstadoAlbum(BaseModel):
    obra_id: int | None = None
    ouvida: bool = False
    favorito: bool = False
    quero_ouvir: bool = False
    nota: float | None = None
    review: str | None = None
    quantidade_escutas: int = 0