"""Limpeza dos contadores expirados. Use --executar para remover."""
import argparse
from time import time

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from backend.app.database import obter_motor
from backend.app.limites_persistentes import limpar_expirados
from backend.app.models import LimiteRequisicao


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--executar", action="store_true")
    args = parser.parse_args()
    motor = obter_motor()
    agora = int(time())
    if args.executar:
        print(f"Contadores removidos: {limpar_expirados(motor, agora=agora)}")
    else:
        with Session(motor) as sessao:
            total = sessao.scalar(select(func.count()).select_from(
                LimiteRequisicao
            ).where(LimiteRequisicao.expira_em <= agora))
        print(f"Simulacao: {total} contadores expirados; nenhum removido.")


if __name__ == "__main__":
    main()
