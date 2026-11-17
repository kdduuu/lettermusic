"""Contratos de dados publicos do perfil social."""
from datetime import datetime

from pydantic import BaseModel, Field


class EstatisticasPerfilPublico(BaseModel):
    avaliacoes: int = Field(ge=0)
    reviews: int = Field(ge=0)
    listas_publicas: int = Field(ge=0)


class AlbumRecentePerfil(BaseModel):
    """Obra com avaliacao ou review publica, nunca escuta privada."""
    id_musicbrainz: str
    titulo: str
    artista: str | None
    registrado_em: datetime


class ReviewRecentePerfil(BaseModel):
    id: int
    obra_id: int
    id_musicbrainz: str
    titulo: str
    artista: str | None
    texto: str
    criada_em: datetime
    atualizada_em: datetime | None


class ListaPublicaPerfil(BaseModel):
    id: int
    titulo: str
    descricao: str | None
    criada_em: datetime


class PerfilSocialPublico(BaseModel):
    id: int
    username: str
    nome_exibicao: str
    bio: str | None
    criado_em: datetime
    estatisticas: EstatisticasPerfilPublico
    albuns_recentes: list[AlbumRecentePerfil]
    reviews_recentes: list[ReviewRecentePerfil]
    listas_publicas: list[ListaPublicaPerfil]