"""Consulta a disponibilidade de capas frontais no Cover Art Archive."""

from uuid import UUID

import httpx

URL_CAPAS = "https://coverartarchive.org/release-group"
HEADERS = {
    "User-Agent": "Lettermusic/0.1 (https://github.com/kdduuu/lettermusic)",
}


def consultar_url_capa(id_musicbrainz: str) -> str | None:
    """Retorna a URL oficial da capa frontal, sem baixar o arquivo de imagem.

    O Cover Art Archive responde com 307 quando há uma imagem de capa
    escolhida para o release-group. O navegador acompanha o redirect
    para a imagem hospedada no Internet Archive.
    """
    mbid = str(UUID(id_musicbrainz))
    url_capa = f"{URL_CAPAS}/{mbid}/front-500"

    resposta = httpx.get(
        url_capa,
        headers=HEADERS,
        timeout=6.0,
        follow_redirects=False,
    )

    if resposta.status_code == 404:
        return None

    if resposta.status_code == 307:
        if not resposta.headers.get("location"):
            raise ValueError("Redirecionamento de capa sem destino.")
        return url_capa

    # Compatibilidade com serviços intermediários que já entregam a imagem.
    if (
        resposta.status_code == 200
        and resposta.headers.get("content-type", "").lower().startswith("image/")
    ):
        return url_capa

    resposta.raise_for_status()
    raise ValueError("Resposta inesperada do Cover Art Archive.")