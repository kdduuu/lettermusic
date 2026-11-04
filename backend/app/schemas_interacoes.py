from datetime import datetime
from decimal import Decimal

from pydantic import (
    AwareDatetime,
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
)


# -----------------------------------------
# OBRAS E ESCUTAS
# -----------------------------------------


class ObraInteracao(BaseModel):
    """Contrato publico: o cliente identifica a obra, sem fornecer metadados."""

    # Aceita os campos antigos, mas os descarta: titulo e artista sempre
    # sao consultados no MusicBrainz ao cadastrar uma obra nova.
    model_config = ConfigDict(extra="ignore")

    id_musicbrainz: str = Field(
        min_length=1,
        max_length=36,
        description="ID do release-group no MusicBrainz.",
    )


class MetadadosObraOficial(BaseModel):
    """Contrato interno da resposta oficial do MusicBrainz (nao do cliente)."""

    id_musicbrainz: str = Field(min_length=1, max_length=36)
    titulo: str = Field(min_length=1, max_length=255)
    artista: str | None = Field(default=None, max_length=255)
    tipo: str | None = Field(default=None, max_length=30)
    data_lancamento: str | None = Field(default=None, max_length=10)


class MarcarOuvidaEntrada(BaseModel):
    obra: ObraInteracao


class RegistrarEscutaEntrada(BaseModel):
    obra: ObraInteracao
    ouvida_em: AwareDatetime | None = None


class ObraOuvidaPublica(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    obra_id: int
    marcada_em: datetime
    id_musicbrainz: str | None = None
    titulo: str | None = None
    artista: str | None = None
    tipo: str | None = None
    data_lancamento: str | None = None


class EscutaPublica(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    obra_id: int
    ouvida_em: datetime
    registrada_em: datetime
    id_musicbrainz: str | None = None
    titulo: str | None = None
    artista: str | None = None
    tipo: str | None = None
    data_lancamento: str | None = None


# -----------------------------------------
# AVALIACOES
# -----------------------------------------


class AvaliacaoCriarEntrada(BaseModel):
    obra: ObraInteracao
    nota: Decimal = Field(
        ge=Decimal("0.5"),
        le=Decimal("5.0"),
        multiple_of=Decimal("0.5"),
    )


class AvaliacaoEditarEntrada(BaseModel):
    nota: Decimal = Field(
        ge=Decimal("0.5"),
        le=Decimal("5.0"),
        multiple_of=Decimal("0.5"),
    )


class AvaliacaoPublica(BaseModel):
    id: int
    obra_id: int
    nota: float
    criada_em: datetime
    atualizada_em: datetime | None
    id_musicbrainz: str | None = None
    titulo: str | None = None
    artista: str | None = None
    tipo: str | None = None
    data_lancamento: str | None = None


class AvaliacaoMediaPublica(BaseModel):
    obra_id: int
    media: float | None
    quantidade: int


# -----------------------------------------
# REVIEWS
# -----------------------------------------


class ReviewEditarEntrada(BaseModel):
    texto: str = Field(min_length=1, max_length=5000)

    @field_validator("texto")
    @classmethod
    def validar_texto(cls, valor: str) -> str:
        texto = valor.strip()

        if not texto:
            raise ValueError(
                "A review nao pode ficar vazia."
            )

        return texto


class ReviewCriarEntrada(ReviewEditarEntrada):
    obra: ObraInteracao


class ReviewPublica(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    usuario_id: int
    obra_id: int
    texto: str
    criada_em: datetime
    atualizada_em: datetime | None
    id_musicbrainz: str | None = None
    titulo: str | None = None
    artista: str | None = None
    tipo: str | None = None
    data_lancamento: str | None = None


# -----------------------------------------
# SPRINT 04 - BIBLIOTECA MUSICAL
# -----------------------------------------


class AdicionarItemBibliotecaEntrada(BaseModel):
    """Dados recebidos ao adicionar uma obra."""

    obra: ObraInteracao


class ItemBibliotecaPublico(BaseModel):
    """Dados devolvidos pela API."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    obra_id: int
    adicionado_em: datetime
    id_musicbrainz: str | None = None
    titulo: str | None = None
    artista: str | None = None
    tipo: str | None = None
    data_lancamento: str | None = None
