
from datetime import datetime

from pydantic import BaseModel, Field


# -----------------------------------------
# ESTATISTICAS DO PERFIL
# -----------------------------------------


class EstatisticasPerfilPublico(BaseModel):
    """Quantidades de interacoes publicas do usuario."""

    avaliacoes: int = Field(ge=0)
    reviews: int = Field(ge=0)
    listas_publicas: int = Field(ge=0)


# -----------------------------------------
# REVIEWS RECENTES
# -----------------------------------------


class ReviewRecentePerfil(BaseModel):
    """Review acompanhada dos dados basicos da obra."""

    id: int
    obra_id: int
    titulo: str
    artista: str | None
    texto: str
    criada_em: datetime
    atualizada_em: datetime | None


# -----------------------------------------
# LISTAS PUBLICAS
# -----------------------------------------


class ListaPublicaPerfil(BaseModel):
    """Lista musical visivel no perfil social."""

    id: int
    titulo: str
    descricao: str | None
    criada_em: datetime


# -----------------------------------------
# PERFIL SOCIAL COMPLETO
# -----------------------------------------


class PerfilSocialPublico(BaseModel):
    """Resposta publica do perfil de um usuario."""

    id: int
    username: str
    nome_exibicao: str
    bio: str | None
    criado_em: datetime

    estatisticas: EstatisticasPerfilPublico

    reviews_recentes: list[ReviewRecentePerfil]
    listas_publicas: list[ListaPublicaPerfil]
