
import os
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.engine import URL
from sqlalchemy.orm import Session


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


@lru_cache(maxsize=1)
def obter_motor():
    return criar_motor()


def obter_sessao():
    with Session(obter_motor()) as sessao:
        yield sessao
