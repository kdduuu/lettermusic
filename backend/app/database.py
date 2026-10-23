
import os
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.engine import URL


# Localiza o arquivo .env na raiz do projeto.
RAIZ_PROJETO = Path(__file__).resolve().parents[2]
load_dotenv(RAIZ_PROJETO / ".env")


def criar_motor():
    usuario = os.getenv("DB_USER")
    senha = os.getenv("DB_PASSWORD")
    nome_banco = os.getenv("DB_NAME")

    if not all([usuario, senha, nome_banco]):
        raise ValueError("Configuracoes do banco incompletas no .env")

    endereco = URL.create(
        "postgresql+psycopg",
        username=usuario,
        password=senha,
        host=os.getenv("DB_HOST", "localhost"),
        port=int(os.getenv("DB_PORT", "5432")),
        database=nome_banco
    )

    return create_engine(endereco)
