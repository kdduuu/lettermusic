
from datetime import datetime

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
)

from backend.app.schemas_interacoes import ObraInteracao


# -----------------------------------------
# CRIACAO DE LISTAS
# -----------------------------------------


class ListaCriarEntrada(BaseModel):
    """Dados recebidos ao criar uma lista."""

    titulo: str = Field(
        min_length=1,
        max_length=120,
    )

    descricao: str | None = Field(
        default=None,
        max_length=500,
    )

    publica: bool = True

    @field_validator("titulo")
    @classmethod
    def validar_titulo(cls, valor: str) -> str:
        titulo = valor.strip()

        if not titulo:
            raise ValueError(
                "O titulo nao pode ficar vazio."
            )

        return titulo

    @field_validator("descricao")
    @classmethod
    def validar_descricao(
        cls,
        valor: str | None,
    ) -> str | None:
        if valor is None:
            return None

        descricao = valor.strip()

        return descricao or None


# -----------------------------------------
# EDICAO DE LISTAS
# -----------------------------------------


class ListaEditarEntrada(ListaCriarEntrada):
    """Exige todos os campos na edicao."""

    descricao: str | None = Field(max_length=500)
    publica: bool


# -----------------------------------------
# RESPOSTA DAS LISTAS
# -----------------------------------------


class ListaPublica(BaseModel):
    """Dados de uma lista devolvidos pela API."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    usuario_id: int
    titulo: str
    descricao: str | None
    publica: bool
    criada_em: datetime
    atualizada_em: datetime | None


# -----------------------------------------
# ITENS DAS LISTAS
# -----------------------------------------


class ItemListaAdicionarEntrada(BaseModel):
    """Dados da obra que sera adicionada."""

    obra: ObraInteracao


class ItemListaPublico(BaseModel):
    """Dados devolvidos para cada item da lista."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    lista_id: int
    obra_id: int
    posicao: int
    adicionado_em: datetime


# -----------------------------------------
# REORDENACAO
# -----------------------------------------


class MoverItemListaEntrada(BaseModel):
    """Nova posicao de um album na lista."""

    nova_posicao: int = Field(ge=1)
