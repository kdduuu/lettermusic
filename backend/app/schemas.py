
from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UsuarioCriar(BaseModel):
    username: str = Field(
        min_length=3,
        max_length=30,
        pattern=r"^[a-zA-Z0-9_]+$"
    )
    nome_exibicao: str = Field(min_length=2, max_length=80)
    email: EmailStr
    senha: str = Field(min_length=12, max_length=128)


class UsuarioPublico(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    nome_exibicao: str
    bio: str | None
    criado_em: datetime


class CredenciaisLogin(BaseModel):
    identificador: str = Field(min_length=3, max_length=254)
    senha: str = Field(min_length=1, max_length=128)


class TokenAcesso(BaseModel):
    access_token: str
    token_type: str = "bearer"
