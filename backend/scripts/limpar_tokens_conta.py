"""Uso:
python -m backend.scripts.limpar_tokens_conta
python -m backend.scripts.limpar_tokens_conta --executar
"""

import argparse

from sqlalchemy.orm import Session

from backend.app.database import obter_motor
from backend.app.limpeza_tokens import (
    contar_tokens,
    limpar_tokens,
)


def main():
    parser = argparse.ArgumentParser(
        description="Limpeza de tokens de conta."
    )
    parser.add_argument(
        "--executar",
        action="store_true",
        help="Excluir os tokens usados ou expirados.",
    )
    argumentos = parser.parse_args()

    with Session(obter_motor()) as sessao:
        quantidade = contar_tokens(sessao)

        if not argumentos.executar:
            print(
                f"Simulacao: {quantidade} tokens "
                "elegiveis para limpeza."
            )
            print("Nenhum registro foi removido.")
            return

        removidos = limpar_tokens(sessao)
        print(f"Tokens removidos: {removidos}")


if __name__ == "__main__":
    main()
