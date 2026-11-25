"""Contratos de dados publicos do perfil social."""
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


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


class AlbumFavoritoPerfil(BaseModel):
    id_musicbrainz: str
    titulo: str
    artista: str | None


class FavoritosPerfilEntrada(BaseModel):
    model_config = ConfigDict(extra="forbid")
    albuns: list[UUID] = Field(max_length=4)

    @field_validator("albuns")
    @classmethod
    def validar_distintos(cls, albuns: list[UUID]) -> list[UUID]:
        if len(set(albuns)) != len(albuns):
            raise ValueError("Os albuns devem ser distintos.")
        return albuns


class PerfilSocialPublico(BaseModel):
    id: int
    username: str
    nome_exibicao: str
    bio: str | None
    criado_em: datetime
    estatisticas: EstatisticasPerfilPublico
    albuns_favoritos: list[AlbumFavoritoPerfil]
    albuns_recentes: list[AlbumRecentePerfil]
    reviews_recentes: list[ReviewRecentePerfil]
    listas_publicas: list[ListaPublicaPerfil]