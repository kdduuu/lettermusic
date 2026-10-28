
from datetime import datetime

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field


class ObraInteracao(BaseModel):
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


class EscutaPublica(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    obra_id: int
    ouvida_em: datetime
    registrada_em: datetime
