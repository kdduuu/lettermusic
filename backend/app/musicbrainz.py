import logging
from collections import OrderedDict
from copy import deepcopy
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from threading import Lock
from time import monotonic as _agora, sleep as _dormir
from uuid import UUID

import httpx

URL_MUSICBRAINZ = "https://musicbrainz.org/ws/2/release-group/"

HEADERS = {
    "User-Agent": "Lettermusic/0.1 (https://github.com/kdduuu/lettermusic)"
}


# Limites locais: um processo Uvicorn, sem Redis ou novas dependencias.
INTERVALO_REQUISICOES = 1.05
TIMEOUT = 5.0
MAX_TENTATIVAS = 2
ESPERA_MAX_RETRY = 3.0
TTL_BUSCA = 300.0
TTL_DETALHE = 3600.0
MAX_CACHE = 512

_logger = logging.getLogger("uvicorn.error")
_cache = OrderedDict()
_lock_cache = Lock()
_lock_rede = Lock()
_proximo_inicio = 0.0
_bloqueado_ate = 0.0

_STATUS_TRANSITORIOS = {429, 500, 502, 503, 504}
_ERROS_TRANSITORIOS = (
    httpx.TimeoutException,
    httpx.NetworkError,
    httpx.RemoteProtocolError,
)


def _retry_after(resposta: httpx.Response) -> float:
    """Interpreta Retry-After em segundos ou em data HTTP."""
    valor = resposta.headers.get("Retry-After")
    if not valor:
        return 0.0
    try:
        return float(max(0, int(valor)))
    except ValueError:
        try:
            data = parsedate_to_datetime(valor)
            if data.tzinfo is None:
                data = data.replace(tzinfo=timezone.utc)
            return max(0.0, (data - datetime.now(timezone.utc)).total_seconds())
        except (ValueError, TypeError, OverflowError):
            return 0.0


def _requisitar(url: str, parametros: dict, operacao: str) -> httpx.Response:
    """Executada sob _lock_rede; todas as tentativas respeitam o intervalo."""
    global _proximo_inicio, _bloqueado_ate

    for tentativa in range(1, MAX_TENTATIVAS + 1):
        espera = max(_proximo_inicio, _bloqueado_ate) - _agora()
        if espera > ESPERA_MAX_RETRY:
            _logger.warning("MusicBrainz %s: cooldown ativo; consulta adiada", operacao)
            raise httpx.RequestError("MusicBrainz em periodo de espera.")
        if espera > 0:
            _dormir(espera)

        _proximo_inicio = _agora() + INTERVALO_REQUISICOES
        try:
            resposta = httpx.get(
                url, params=parametros, headers=HEADERS, timeout=TIMEOUT,
            )
        except _ERROS_TRANSITORIOS as erro:
            _logger.warning(
                "MusicBrainz %s: %s (tentativa %d/%d)",
                operacao, type(erro).__name__, tentativa, MAX_TENTATIVAS,
            )
            if tentativa == MAX_TENTATIVAS:
                raise
            _bloqueado_ate = max(_bloqueado_ate, _agora() + 1.0)
            continue
        except httpx.HTTPError as erro:
            _logger.warning("MusicBrainz %s: %s", operacao, type(erro).__name__)
            raise

        status = resposta.status_code
        if status == 404 and operacao == "detalhe":
            return resposta

        try:
            resposta.raise_for_status()
        except httpx.HTTPStatusError as erro:
            _logger.warning(
                "MusicBrainz %s: HTTP %s (tentativa %d/%d)",
                operacao, erro.response.status_code, tentativa, MAX_TENTATIVAS,
            )
            if erro.response.status_code not in _STATUS_TRANSITORIOS:
                raise
            espera_retry = max(2.0, _retry_after(erro.response))
            _bloqueado_ate = max(_bloqueado_ate, _agora() + espera_retry)
            if tentativa == MAX_TENTATIVAS or espera_retry > ESPERA_MAX_RETRY:
                raise
            continue
        return resposta

    raise RuntimeError("Fluxo de tentativas inesperado.")


def _chave_cache(url, parametros):
    return (url, tuple(sorted(parametros.items())))


def _ler_cache(chave):
    with _lock_cache:
        entrada = _cache.get(chave)
        if entrada is not None:
            validade, dados = entrada
            if _agora() < validade:
                _cache.move_to_end(chave)
                return True, deepcopy(dados)
            del _cache[chave]
        return False, None


def _guardar_cache(chave, dados, ttl):
    with _lock_cache:
        agora = _agora()
        for antiga in [k for k, (validade, _) in _cache.items() if validade <= agora]:
            del _cache[antiga]
        _cache[chave] = (agora + ttl, deepcopy(dados))
        _cache.move_to_end(chave)
        while len(_cache) > MAX_CACHE:
            _cache.popitem(last=False)


def _consultar(url, parametros, operacao, ttl, interpretar):
    chave = _chave_cache(url, parametros)
    encontrado, dados = _ler_cache(chave)
    if encontrado:
        _logger.debug("MusicBrainz %s: cache hit", operacao)
        return dados

    # Cache hits nao esperam uma consulta de rede em andamento.
    # Espera limitada para evitar acumular uma fila indefinida.
    if not _lock_rede.acquire(timeout=3.0):
        _logger.warning("MusicBrainz %s: fila local ocupada", operacao)
        raise httpx.RequestError("Fila do MusicBrainz ocupada.")
    try:
        encontrado, dados = _ler_cache(chave)
        if encontrado:
            return dados
        resposta = _requisitar(url, parametros, operacao)
        if operacao == "detalhe" and resposta.status_code == 404:
            return None
        try:
            dados = interpretar(resposta.json())
        except (ValueError, TypeError, AttributeError) as erro:
            _logger.warning("MusicBrainz %s: resposta invalida", operacao)
            if operacao == "busca":
                # A rota de busca ja converte HTTPError em 502.
                raise httpx.DecodingError("Resposta inesperada do MusicBrainz.") from erro
            raise ValueError("Resposta inesperada do MusicBrainz.") from erro
        _guardar_cache(chave, dados, ttl)
        return dados
    finally:
        _lock_rede.release()


def escapar_consulta(texto: str) -> str:
    """Protege caracteres especiais usados na busca."""
    return texto.replace("\\", "\\\\").replace('"', '\\"')


def extrair_artista(creditos: list) -> str | None:
    """Monta o nome exibido a partir dos creditos do MusicBrainz."""
    if not isinstance(creditos, list):
        raise ValueError("Creditos MusicBrainz invalidos.")
    partes = []

    for credito in creditos:
        if isinstance(credito, dict):
            nome = credito.get("name", "")
            separador = credito.get("joinphrase", "")
            if not isinstance(nome, str) or not isinstance(separador, str):
                raise ValueError("Creditos MusicBrainz invalidos.")
            partes.append(nome + separador)

    return "".join(partes).strip() or None


def pesquisar_obras(termo: str, artista: str | None = None) -> list[dict]:
    parametros = {
        "query": termo,
        "fmt": "json",
        "limit": 5,
        "dismax": "true",
    }

    if artista:
        titulo_seguro = escapar_consulta(termo)
        artista_seguro = escapar_consulta(artista)

        parametros["query"] = (
            f'releasegroup:"{titulo_seguro}" '
            f'AND artist:"{artista_seguro}"'
        )
        parametros["dismax"] = "false"

    return _consultar(
        URL_MUSICBRAINZ, parametros, "busca", TTL_BUSCA, _interpretar_busca,
    )


def _interpretar_busca(dados: dict) -> list[dict]:
    if not isinstance(dados, dict) or not isinstance(dados.get("release-groups"), list):
        raise ValueError("Resposta inesperada do MusicBrainz.")
    if any(not isinstance(grupo, dict) for grupo in dados["release-groups"]):
        raise ValueError("Resposta inesperada do MusicBrainz.")

    obras = []

    for grupo in dados.get("release-groups", []):
        obras.append(
            {
                "id_musicbrainz": grupo.get("id"),
                "titulo": grupo.get("title"),
                "artista": extrair_artista(
                    grupo.get("artist-credit", [])
                ),
                "tipo": grupo.get("primary-type"),
                "data_lancamento": grupo.get("first-release-date"),
            }
        )

    return obras


def consultar_obra_por_id(id_musicbrainz: str) -> dict | None:
    """Busca metadados oficiais de um release-group pelo seu MBID."""
    try:
        mbid = str(UUID(id_musicbrainz))
    except (ValueError, AttributeError, TypeError) as erro:
        raise ValueError("ID MusicBrainz invalido.") from erro

    return _consultar(
        f"{URL_MUSICBRAINZ}{mbid}",
        {"fmt": "json", "inc": "artist-credits"},
        "detalhe", TTL_DETALHE,
        lambda grupo: _interpretar_detalhe(grupo, mbid),
    )


def _interpretar_detalhe(grupo: dict, mbid: str) -> dict:
    if (
        not isinstance(grupo, dict)
        or grupo.get("id") != mbid
        or not isinstance(grupo.get("title"), str)
        or not grupo["title"].strip()
    ):
        raise ValueError("Resposta inesperada do MusicBrainz.")

    return {
        "id_musicbrainz": mbid,
        "titulo": grupo["title"],
        "artista": extrair_artista(grupo.get("artist-credit", [])),
        "tipo": grupo.get("primary-type"),
        "data_lancamento": grupo.get("first-release-date"),
    }