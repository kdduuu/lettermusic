"""Adaptador HTTP para o limitador persistente."""
import os
import logging
from ipaddress import ip_address

from fastapi import HTTPException, Request
from sqlalchemy.exc import SQLAlchemyError

from backend.app.limites_persistentes import (
    LimiteExcedido, RegraLimite, chave_limite, reservar,
)

LOGGER = logging.getLogger(__name__)


def origem_requisicao(request: Request) -> str:
    """Somente a origem ASGI; nao interpreta headers fornecidos pelo cliente.

    O servidor ASGI deve confiar apenas em proxies conhecidos. Ate a
    configuracao do ingresso, requisicoes via Next compartilham sua origem.
    """
    if request.client is None:
        return "desconhecido"
    try:
        endereco = ip_address(request.client.host)
        if getattr(endereco, "ipv4_mapped", None):
            endereco = endereco.ipv4_mapped
        return endereco.compressed
    except ValueError:
        return "desconhecido"


def aplicar_limites(motor, politicas, mensagem):
    segredo = os.getenv("RATE_LIMIT_SECRET") or os.getenv("JWT_SECRET", "")
    if len(segredo) < 32:
        raise HTTPException(503, "Protecao temporariamente indisponivel.")
    regras = [
        RegraLimite(chave_limite(escopo, valor, segredo), maximo, janela)
        for escopo, valor, maximo, janela in politicas
    ]
    try:
        reservar(motor, regras)
    except LimiteExcedido as erro:
        raise HTTPException(
            429, mensagem, headers={"Retry-After": str(erro.aguardar)}
        ) from None
    except SQLAlchemyError:
        LOGGER.warning("Limitador persistente indisponivel.")
        raise HTTPException(503, "Protecao temporariamente indisponivel.") from None
