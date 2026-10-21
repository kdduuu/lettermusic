
import httpx

URL_MUSICBRAINZ = "https://musicbrainz.org/ws/2/release-group/"

HEADERS = {
    "User-Agent": "Lettermusic/0.1 (https://github.com/kdduuu/lettermusic)"
}


def escapar_consulta(texto):
    # Protege caracteres que poderiam alterar a sintaxe da pesquisa.
    return texto.replace("\\", "\\\\").replace('"', '\\"')


def pesquisar_obras(termo, artista=None):
    parametros = {
        "query": termo,
        "fmt": "json",
        "limit": 5,
        "dismax": "true"
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
        timeout=15.0
    )

    resposta.raise_for_status()
    dados = resposta.json()

    obras = []

    for grupo in dados.get("release-groups", []):
        partes_artista = []

        for credito in grupo.get("artist-credit", []):
            if isinstance(credito, dict):
                nome = credito.get("name", "")
                separador = credito.get("joinphrase", "")
                partes_artista.append(nome + separador)

        nome_artista = "".join(partes_artista).strip() or None

        obras.append({
            "id_musicbrainz": grupo.get("id"),
            "titulo": grupo.get("title"),
            "artista": nome_artista,
            "tipo": grupo.get("primary-type"),
            "data_lancamento": grupo.get("first-release-date")
        })

    return obras
