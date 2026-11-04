"""Operacoes de insercao atomica compativeis com PostgreSQL e SQLite."""

from sqlalchemy.dialects.postgresql import insert as inserir_postgres
from sqlalchemy.dialects.sqlite import insert as inserir_sqlite
from sqlalchemy.orm import Session


def inserir_se_ausente(
    sessao: Session,
    modelo,
    valores: dict,
    colunas_unicas: list,
) -> None:
    """Faz INSERT sem duplicar pela chave informada, sem executar commit.

    O proprio banco decide qual insercao vence uma disputa simultanea.
    Outros erros de integridade continuam sendo propagados.
    """

    dialeto = sessao.get_bind().dialect.name

    if dialeto == "postgresql":
        inserir = inserir_postgres
    elif dialeto == "sqlite":
        inserir = inserir_sqlite
    else:
        raise RuntimeError(f"Banco nao suportado: {dialeto}")

    instrucao = (
        inserir(modelo)
        .values(**valores)
        .on_conflict_do_nothing(index_elements=colunas_unicas)
    )

    sessao.execute(instrucao)
