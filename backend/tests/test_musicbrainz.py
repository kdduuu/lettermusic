
from unittest.mock import patch

from backend.app.musicbrainz import pesquisar_obras


def test_pesquisa_identifica_artistas():
    dados_simulados = {
        "release-groups": [
            {
                "title": "OK Computer",
                "artist-credit": [
                    {"name": "Radiohead"}
                ]
            },
            {
                "title": "Música em parceria",
                "artist-credit": [
                    {"name": "Artista A", "joinphrase": " & "},
                    {"name": "Artista B"}
                ]
            }
        ]
    }

    with patch("backend.app.musicbrainz.httpx.get") as requisicao:
        requisicao.return_value.json.return_value = dados_simulados

        obras = pesquisar_obras("OK Computer")

    assert obras[0]["artista"] == "Radiohead"
    assert obras[1]["artista"] == "Artista A & Artista B"
