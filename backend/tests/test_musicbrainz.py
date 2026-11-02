
from unittest.mock import patch

import httpx
import pytest

from backend.app.musicbrainz import (
    consultar_obra_por_id,
    pesquisar_obras,
)


# -----------------------------------------
# TESTES EXISTENTES - PESQUISA MUSICAL
# -----------------------------------------


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


def test_pesquisa_filtra_por_artista():
    with patch("backend.app.musicbrainz.httpx.get") as requisicao:
        requisicao.return_value.json.return_value = {
            "release-groups": []
        }

        pesquisar_obras("OK Computer", "Radiohead")

    parametros = requisicao.call_args.kwargs["params"]

    assert parametros["query"] == (
        'releasegroup:"OK Computer" AND artist:"Radiohead"'
    )
    assert parametros["dismax"] == "false"


# -----------------------------------------
# TESTES NOVOS - CONSULTA POR ID
# -----------------------------------------


def test_consulta_por_id_retorna_dados_oficiais():
    mbid = "b1392450-e666-3926-a536-22c65f834433"

    dados_simulados = {
        "id": mbid,
        "title": "OK Computer",
        "artist-credit": [
            {"name": "Radiohead"}
        ],
        "primary-type": "Album",
        "first-release-date": "1997-05-21",
    }

    with patch("backend.app.musicbrainz.httpx.get") as requisicao:
        requisicao.return_value.status_code = 200
        requisicao.return_value.json.return_value = dados_simulados

        obra = consultar_obra_por_id(mbid.upper())

    assert obra == {
        "id_musicbrainz": mbid,
        "titulo": "OK Computer",
        "artista": "Radiohead",
        "tipo": "Album",
        "data_lancamento": "1997-05-21",
    }

    argumentos = requisicao.call_args

    assert argumentos.args[0].endswith(mbid)
    assert argumentos.kwargs["params"] == {
        "fmt": "json",
        "inc": "artist-credits",
    }


@pytest.mark.parametrize(
    "mbid_invalido",
    [
        "id-inventado",
        "",
    ],
)
def test_consulta_rejeita_id_invalido(mbid_invalido):
    with patch("backend.app.musicbrainz.httpx.get") as requisicao:
        with pytest.raises(ValueError, match="ID MusicBrainz invalido"):
            consultar_obra_por_id(mbid_invalido)

    requisicao.assert_not_called()


def test_consulta_obra_inexistente_retorna_none():
    mbid = "b1392450-e666-3926-a536-22c65f834433"

    with patch("backend.app.musicbrainz.httpx.get") as requisicao:
        requisicao.return_value.status_code = 404

        resultado = consultar_obra_por_id(mbid)

    assert resultado is None


def test_consulta_rejeita_id_diferente_na_resposta():
    mbid = "b1392450-e666-3926-a536-22c65f834433"

    dados_simulados = {
        "id": "00000000-0000-4000-8000-000000000001",
        "title": "Outro album",
    }

    with patch("backend.app.musicbrainz.httpx.get") as requisicao:
        requisicao.return_value.status_code = 200
        requisicao.return_value.json.return_value = dados_simulados

        with pytest.raises(ValueError, match="Resposta inesperada"):
            consultar_obra_por_id(mbid)


def test_consulta_rejeita_obra_sem_titulo():
    mbid = "b1392450-e666-3926-a536-22c65f834433"

    dados_simulados = {
        "id": mbid,
        "title": "",
    }

    with patch("backend.app.musicbrainz.httpx.get") as requisicao:
        requisicao.return_value.status_code = 200
        requisicao.return_value.json.return_value = dados_simulados

        with pytest.raises(ValueError, match="Resposta inesperada"):
            consultar_obra_por_id(mbid)


def test_consulta_propaga_erro_do_musicbrainz():
    mbid = "b1392450-e666-3926-a536-22c65f834433"

    pedido = httpx.Request(
        "GET",
        f"https://musicbrainz.org/ws/2/release-group/{mbid}",
    )

    resposta_erro = httpx.Response(
        503,
        request=pedido,
    )

    with patch("backend.app.musicbrainz.httpx.get") as requisicao:
        requisicao.return_value = resposta_erro

        with pytest.raises(httpx.HTTPStatusError):
            consultar_obra_por_id(mbid)
