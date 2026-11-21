from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


class ContaPrivada(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    nome_exibicao: str
    email: EmailStr
    email_confirmado: bool


class AtualizarContaEntrada(BaseModel):
    nome_exibicao: str = Field(min_length=2, max_length=80)

    @field_validator("nome_exibicao")
    @classmethod
    def limpar_nome(cls, nome):
        nome = nome.strip()
        if len(nome) < 2:
            raise ValueError("Informe um nome de exibicao valido.")
        return nome


class AlterarSenhaEntrada(BaseModel):
    senha_atual: str = Field(min_length=1, max_length=128)
    senha_nova: str = Field(min_length=12, max_length=128)


class ExcluirContaEntrada(BaseModel):
    senha_atual: str = Field(min_length=1, max_length=128)
