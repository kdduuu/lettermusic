"""Reserva atomica de tentativas em janelas fixas, compartilhadas pelo banco.

O limitador tem transacao propria: a reserva nao depende do resultado da
operacao de negocio. A camada HTTP decide as chaves, politicas e resposta.
"""

from dataclasses import dataclass
from hashlib import sha256
import hmac
from time import time

from sqlalchemy import case, delete, or_, select
from sqlalchemy.dialects.postgresql import insert as insert_pg
from sqlalchemy.dialects.sqlite import insert as insert_sqlite
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session

from backend.app.models import LimiteRequisicao


@dataclass(frozen=True)
class RegraLimite:
    chave: str
    maximo: int
    janela: int


class LimiteExcedido(Exception):
    def __init__(self, aguardar: int):
        super().__init__("Limite de requisicoes excedido.")
        self.aguardar = aguardar


def chave_limite(escopo: str, identificador: str, segredo: str) -> str:
    """Nao armazena IP ou identificador em texto aberto."""
    if not escopo or not identificador or not segredo:
        raise ValueError("Chave de limite incompleta.")
    mensagem = f"{escopo}\0{identificador}".encode("utf-8")
    return hmac.new(segredo.encode("utf-8"), mensagem, sha256).hexdigest()


def reservar(motor: Engine, regras: list[RegraLimite], *, agora: int | None = None):
    """Reserva uma tentativa para todas as regras ou nenhuma.

    A janela comeca na primeira tentativa aceita. UPSERT condicional evita
    a corrida entre verificar e incrementar, inclusive em processos distintos.
    A ordenacao das chaves mantem uma ordem consistente de bloqueio.
    """
    if not regras or len({r.chave for r in regras}) != len(regras):
        raise ValueError("Informe regras distintas.")
    if any(
        len(r.chave) != 64
        or any(c not in "0123456789abcdef" for c in r.chave)
        or r.maximo <= 0
        or r.janela <= 0
        for r in regras
    ):
        raise ValueError("Regra de limite invalida.")

    if motor.dialect.name == "postgresql":
        inserir = insert_pg
    elif motor.dialect.name == "sqlite":
        inserir = insert_sqlite
    else:
        raise ValueError("Banco nao suportado pelo limitador.")

    instante = int(time()) if agora is None else agora
    tabela = LimiteRequisicao.__table__
    c = tabela.c

    with Session(motor) as sessao, sessao.begin():
        for regra in sorted(regras, key=lambda r: r.chave):
            expirada = c.expira_em <= instante
            comando = inserir(tabela).values(
                chave=regra.chave,
                quantidade=1,
                expira_em=instante + regra.janela,
            )
            comando = comando.on_conflict_do_update(
                index_elements=[c.chave],
                set_={
                    "quantidade": case((expirada, 1), else_=c.quantidade + 1),
                    "expira_em": case(
                        (expirada, instante + regra.janela),
                        else_=c.expira_em,
                    ),
                },
                where=or_(expirada, c.quantidade < regra.maximo),
            ).returning(c.quantidade)

            if sessao.scalar(comando) is None:
                expiracao = sessao.scalar(
                    select(c.expira_em).where(c.chave == regra.chave)
                )
                raise LimiteExcedido(max(1, expiracao - instante))


def limpar_expirados(motor: Engine, *, agora: int | None = None) -> int:
    """Remove contadores vencidos; executar em manutencao periodica."""
    instante = int(time()) if agora is None else agora
    with Session(motor) as sessao, sessao.begin():
        resultado = sessao.execute(
            delete(LimiteRequisicao).where(LimiteRequisicao.expira_em <= instante)
        )
        return resultado.rowcount
