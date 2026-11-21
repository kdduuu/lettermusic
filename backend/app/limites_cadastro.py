"""Limites locais para criacao de contas."""

from collections import deque
from hashlib import sha256
from threading import Lock
from time import monotonic

from fastapi import HTTPException


JANELA = 900.0
LIMITE_ORIGEM = 12
LIMITE_EMAIL = 3

_lock = Lock()
_eventos = {}
_agora = monotonic


def hash_identificador(valor):
    return sha256(valor.encode("utf-8")).hexdigest()


def verificar_cadastro(ip, email):
    chaves = [
        (
            "cadastro-ip:" + hash_identificador(ip),
            LIMITE_ORIGEM,
        ),
        (
            "cadastro-email:" + hash_identificador(
                email.strip().casefold()
            ),
            LIMITE_EMAIL,
        ),
    ]

    agora = _agora()

    with _lock:
        for chave, limite in chaves:
            registros = _eventos.get(chave)

            if registros is None:
                registros = deque()
                _eventos[chave] = registros

            while registros and registros[0] <= agora - JANELA:
                registros.popleft()

            if len(registros) >= limite:
                raise HTTPException(
                    status_code=429,
                    detail="Muitas tentativas de cadastro. Aguarde.",
                    headers={"Retry-After": "900"},
                )

        for chave, _ in chaves:
            _eventos[chave].append(agora)

        if len(_eventos) > 4096:
            for chave in list(_eventos)[:1024]:
                if not _eventos[chave]:
                    _eventos.pop(chave, None)
