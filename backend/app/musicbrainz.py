
import httpx

URL_MUSICBRAINZ = "https://musicbrainz.org/ws/2/release-group/"

HEADERS = {
    "User-Agent": "Lettermusic/0.1 (https://github.com/kdduuu/lettermusic)"
}


def pesquisar_obras(termo):
    resposta = httpx.get(
        URL_MUSICBRAINZ,
        params={
            "query": termo,
            "fmt": "json",
            "limit": 5,
            "dismax": "true"
        },
        headers=HEADERS,
        timeout=15.0
    )

    resposta.raise_for_status()
    dados = resposta.json()

    obras = []

    for grupo in dados.get("release-groups", []):
        obras.append({
            "id_musicbrainz": grupo.get("id"),
            "titulo": grupo.get("title"),
            "tipo": grupo.get("primary-type"),
            "data_lancamento": grupo.get("first-release-date")
        })

    return obras
