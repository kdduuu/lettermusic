from pydantic import BaseModel, EmailStr, Field


class SolicitarRecuperacao(BaseModel):
    email: EmailStr


class TokenRecebido(BaseModel):
    token: str = Field(min_length=32, max_length=128)


class RedefinirSenha(BaseModel):
    token: str = Field(min_length=32, max_length=128)
    senha_nova: str = Field(min_length=12, max_length=128)
