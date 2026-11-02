
from uuid import UUID

import httpx

URL_MUSICBRAINZ = "https://musicbrainz.org/ws/2/release-group/"

HEADERS = {
    "User-Agent": "Lettermusic/0.1 (https://github.com/kdduuu/lettermusic)"
}


def escapar_consulta(texto: str) -> str:
    """Protege caracteres especiais usados na busca."""
    return texto.replace("\\", "\\\\").replace('"', '\\"')


def extrair_artista(creditos: list) -> str | None:
    """Monta o nome exibido a partir dos creditos do MusicBrainz."""
    partes = []

    for credito in creditos:
        if isinstance(credito, dict):
            nome = credito.get("name", "")
            separador = credito.get("joinphrase", "")
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

    resposta = httpx.get(
        URL_MUSICBRAINZ,
        params=parametros,
        headers=HEADERS,
        timeout=15.0,
    )
    resposta.raise_for_status()
    dados = resposta.json()

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

    resposta = httpx.get(
        f"{URL_MUSICBRAINZ}{mbid}",
        params={"fmt": "json", "inc": "artist-credits"},
        headers=HEADERS,
        timeout=15.0,
    )

    if resposta.status_code == 404:
        return None

    resposta.raise_for_status()
    grupo = resposta.json()

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
