"""Limitacao local de tentativas malsucedidas de autenticacao."""
from collections import deque
from hashlib import sha256
from threading import Lock
from time import monotonic

from fastapi import HTTPException

_lock = Lock()
_falhas = {}
_agora = monotonic
JANELA = 60.0
LIMITE_CONTA = 5
LIMITE_ORIGEM = 40


def _chaves(ip, identificador):
    conta = sha256(
        identificador.strip().casefold().encode()
    ).hexdigest()
    origem = sha256(ip.encode()).hexdigest()
    # Um mesmo identificador compartilha o limite entre IPs.
    return (f"conta:{conta}", f"origem:{origem}")


def _prunear(chave, agora):
    registros = _falhas.get(chave)

    if registros is None:
        return deque()

    while registros and registros[0] <= agora - JANELA:
        registros.popleft()

    if not registros:
        _falhas.pop(chave, None)
        return deque()

    return registros


def verificar(ip, identificador):
    conta, origem = _chaves(ip, identificador)

    with _lock:
        agora = _agora()
        a = len(_prunear(conta, agora))
        b = len(_prunear(origem, agora))

    if a >= LIMITE_CONTA or b >= LIMITE_ORIGEM:
        raise HTTPException(
            status_code=429,
            detail="Muitas tentativas. Tente novamente em um minuto.",
            headers={"Retry-After": "60"},
        )


def registrar_falha(ip, identificador):
    with _lock:
        agora = _agora()

        for chave in _chaves(ip, identificador):
            registros = _prunear(chave, agora)
            registros.append(agora)
            _falhas[chave] = registros

        # Protecao basica contra crescimento ilimitado da memoria.
        if len(_falhas) > 4096:
            for chave in list(_falhas)[:1024]:
                _falhas.pop(chave, None)


def registrar_sucesso(ip, identificador):
    conta, _ = _chaves(ip, identificador)

    with _lock:
        _falhas.pop(conta, None)
