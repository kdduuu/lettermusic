"""Popularidade opcional, sem dependencia do catalogo principal."""
from collections import OrderedDict
from copy import deepcopy
from math import isfinite
from threading import Lock
from time import monotonic, sleep
from uuid import UUID
import logging
import os

import httpx

BASE = "https://api.listenbrainz.org/1/popularity"
TTL = 86400
TTL_VAZIO = 300
TTL_OBSOLETO = 7 * 86400
MAX_CACHE = 256
MAX_IDS = 60
INTERVALO = 1.05
TIMEOUT = 2.5

ENTIDADES = {
    "artistas": ("artist", "artist_mbids", "artist_mbid"),
    "albuns": ("release-group", "release_group_mbids", "release_group_mbid"),
    "faixas": ("recording", "recording_mbids", "recording_mbid"),
}

_cache = OrderedDict()
_lock = Lock()
_lock_rede = Lock()
_bloqueado_ate = 0.0
_proximo_inicio = 0.0
_agora = monotonic
_dormir = sleep

_logger = logging.getLogger("uvicorn.error")


def _token():
    habilitado = os.getenv("LISTENBRAINZ_ENABLED", "true")
    if habilitado.strip().lower() not in {"true", "1", "yes"}:
        return ""
    return os.getenv("LISTENBRAINZ_TOKEN", "").strip()


def _mbid(valor):
    try:
        return str(UUID(str(valor)))
    except (ValueError, TypeError, AttributeError):
        return None


def _texto(valor):
    return valor.strip() if isinstance(valor, str) and valor.strip() else None


def _contagem(valor):
    return valor if type(valor) is int and valor >= 0 else 0


def _segundos(valor):
    try:
        numero = float(valor)
        return numero if isfinite(numero) and numero > 0 else 0.0
    except (TypeError, ValueError):
        return 0.0


def _ler_cache(chave):
    with _lock:
        entrada = _cache.get(chave)

        if entrada is None:
            return False, None

        validade, validade_obsoleta, dados = entrada
        agora = _agora()

        if agora >= validade_obsoleta:
            del _cache[chave]
            return False, None

        _cache.move_to_end(chave)
        return agora < validade, deepcopy(dados)


def _guardar_cache(chave, dados):
    agora = _agora()
    ttl = TTL if dados else TTL_VAZIO

    with _lock:
        _cache[chave] = (
            agora + ttl,
            agora + (TTL_OBSOLETO if dados else TTL_VAZIO),
            deepcopy(dados),
        )
        _cache.move_to_end(chave)

        while len(_cache) > MAX_CACHE:
            _cache.popitem(last=False)


def _consultar(chave, endpoint, interpretar, corpo=None):
    global _bloqueado_ate, _proximo_inicio

    token = _token()

    # Sem token ou integracao desativada: nenhuma chamada externa.
    if not token:
        return None

    fresco, anterior = _ler_cache(chave)

    if fresco:
        return anterior

    # Evita acumular requisicoes esperando pelo servico opcional.
    if not _lock_rede.acquire(blocking=False):
        return anterior

    try:
        fresco, anterior = _ler_cache(chave)

        if fresco:
            return anterior

        agora = _agora()

        if agora < _bloqueado_ate:
            return anterior

        espera = max(0.0, _proximo_inicio - agora)

        if espera > INTERVALO:
            return anterior

        if espera:
            _dormir(espera)

        _proximo_inicio = _agora() + INTERVALO

        headers = {
            "Authorization": f"Token {token}",
            "User-Agent": (
                "Lettermusic/0.1 "
                "(https://github.com/kdduuu/lettermusic)"
            ),
        }

        try:
            if corpo is None:
                resposta = httpx.get(
                    f"{BASE}/{endpoint}",
                    headers=headers,
                    timeout=TIMEOUT,
                )
            else:
                resposta = httpx.post(
                    f"{BASE}/{endpoint}",
                    json=corpo,
                    headers=headers,
                    timeout=TIMEOUT,
                )

            reset = _segundos(
                resposta.headers.get("X-RateLimit-Reset-In")
            )
            retry = _segundos(
                resposta.headers.get("Retry-After")
            )

            if resposta.headers.get("X-RateLimit-Remaining") == "0":
                _bloqueado_ate = max(
                    _bloqueado_ate,
                    _agora() + max(INTERVALO, reset, retry),
                )

            if resposta.status_code == 429:
                _bloqueado_ate = max(
                    _bloqueado_ate,
                    _agora() + max(60, reset, retry),
                )

            resposta.raise_for_status()

            registros = resposta.json()

            if not isinstance(registros, list):
                raise ValueError("Resposta ListenBrainz invalida.")

            dados = interpretar(registros)

        except httpx.HTTPStatusError as erro:
            status = erro.response.status_code
            intervalo = 300 if status in {401, 403} else 60

            _bloqueado_ate = max(
                _bloqueado_ate, _agora() + intervalo
            )

            # Nunca registrar token, cabecalhos ou corpo da resposta.
            _logger.warning(
                "ListenBrainz: HTTP %s; usando fallback", status
            )
            return anterior

        except (httpx.HTTPError, ValueError, TypeError):
            _bloqueado_ate = max(
                _bloqueado_ate, _agora() + 60
            )
            _logger.warning(
                "ListenBrainz indisponivel; usando fallback"
            )
            return anterior

        _guardar_cache(chave, dados)
        return dados

    finally:
        _lock_rede.release()


def obter_popularidade(categoria: str, ids: list[str]) -> dict[str, int]:
    ids = sorted({
        valido for valor in ids
        if (valido := _mbid(valor))
    })[:MAX_IDS]

    if len(ids) < 2:
        return {}

    endpoint, campo_entrada, campo_saida = ENTIDADES[categoria]
    permitidos = set(ids)

    def interpretar(registros):
        dados = {}

        for registro in registros:
            if not isinstance(registro, dict):
                continue

            identificador = _mbid(registro.get(campo_saida))
            ouvintes = registro.get("total_user_count")

            if (
                identificador in permitidos
                and type(ouvintes) is int
                and ouvintes >= 0
            ):
                dados[identificador] = ouvintes

        return dados

    return _consultar(
        ("lote", categoria, tuple(ids)),
        endpoint,
        interpretar,
        {campo_entrada: ids},
    ) or {}


def obter_destaques(categoria: str, artista_id: str) -> list[dict]:
    artista_id = _mbid(artista_id)

    if not artista_id or categoria not in {"albuns", "faixas"}:
        return []

    endpoint = (
        "top-release-groups-for-artist"
        if categoria == "albuns"
        else "top-recordings-for-artist"
    )

    def interpretar(registros):
        itens = {}

        for registro in registros:
            if not isinstance(registro, dict):
                continue

            if categoria == "albuns":
                grupo = registro.get("release_group")
                artista = registro.get("artist")

                if not isinstance(grupo, dict):
                    continue

                artista = artista if isinstance(artista, dict) else {}

                # Usa o release-group, nunca o ID de uma edicao.
                identificador = _mbid(registro.get("release_group_mbid"))
                titulo = _texto(grupo.get("name"))
                nome_artista = _texto(artista.get("name"))
                tipo = _texto(grupo.get("type"))
                data = _texto(grupo.get("date"))

            else:
                identificador = _mbid(registro.get("recording_mbid"))
                titulo = _texto(registro.get("recording_name"))
                nome_artista = _texto(registro.get("artist_name"))
                tipo = "Faixa"
                data = None

                creditos = registro.get("artist_mbids")

                if isinstance(creditos, list) and creditos:
                    if artista_id not in {
                        _mbid(valor) for valor in creditos
                    }:
                        continue

            ouvintes = _contagem(registro.get("total_user_count"))
            escutas = _contagem(registro.get("total_listen_count"))

            if not identificador or not titulo or not (ouvintes or escutas):
                continue

            item = {
                "id_musicbrainz": identificador,
                "titulo": titulo,
                "artista": nome_artista,
                "tipo": tipo,
                "data": data,
                "ouvintes": ouvintes,
                "escutas": escutas,
            }

            existente = itens.get(identificador)

            if existente is None or ouvintes > existente["ouvintes"]:
                itens[identificador] = item

        # Na categoria albuns, prioriza Album sobre singles e EPs.
        # Dentro de cada grupo, ordena por ouvintes e escutas.
        return sorted(
            itens.values(),
            key=lambda item: (
                categoria == "albuns" and item["tipo"] != "Album",
                -item["ouvintes"],
                -item["escutas"],
                item["id_musicbrainz"],
            ),
        )[:MAX_IDS]

    return _consultar(
        ("destaques", categoria, artista_id),
        f"{endpoint}/{artista_id}",
        interpretar,
    ) or []
