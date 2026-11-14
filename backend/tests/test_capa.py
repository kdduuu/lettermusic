from unittest.mock import patch

import httpx
import pytest
from fastapi.testclient import TestClient

from backend.app.cover_art import consultar_url_capa
from backend.app.main import app

client = TestClient(app)
MBID = "b1392450-e666-3926-a536-22c65f834433"
URL_CAPA = f"https://coverartarchive.org/release-group/{MBID}/front-500"


def resposta_externa(status: int, *, headers: dict[str, str] | None = None) -> httpx.Response:
    return httpx.Response(
        status,
        headers=headers or {},
        request=httpx.Request("GET", URL_CAPA),
    )


def test_servico_aceita_307_e_retorna_url_oficial():
    retorno = resposta_externa(
        307,
        headers={"location": "https://archive.org/download/exemplo/capa.jpg"},
    )
    with patch("backend.app.cover_art.httpx.get", return_value=retorno) as requisicao:
        url = consultar_url_capa(MBID.upper())

    assert url == URL_CAPA
    assert requisicao.call_args.args == (URL_CAPA,)
    assert requisicao.call_args.kwargs["follow_redirects"] is False


def test_servico_retorna_none_quando_capa_nao_existe():
    with patch("backend.app.cover_art.httpx.get", return_value=resposta_externa(404)):
        assert consultar_url_capa(MBID) is None


def test_servico_aceita_resposta_direta_de_imagem():
    retorno = resposta_externa(200, headers={"content-type": "image/jpeg"})
    with patch("backend.app.cover_art.httpx.get", return_value=retorno):
        assert consultar_url_capa(MBID) == URL_CAPA


def test_servico_rejeita_redirecionamento_sem_destino():
    with patch("backend.app.cover_art.httpx.get", return_value=resposta_externa(307)):
        with pytest.raises(ValueError, match="sem destino"):
            consultar_url_capa(MBID)


def test_servico_rejeita_resposta_200_sem_imagem():
    retorno = resposta_externa(200, headers={"content-type": "application/json"})
    with patch("backend.app.cover_art.httpx.get", return_value=retorno):
        with pytest.raises(ValueError, match="Resposta inesperada"):
            consultar_url_capa(MBID)


def test_servico_propaga_erro_externo():
    with patch("backend.app.cover_art.httpx.get", return_value=resposta_externa(503)):
        with pytest.raises(httpx.HTTPStatusError):
            consultar_url_capa(MBID)


def test_rota_retorna_url_da_capa():
    with patch(
        "backend.app.rotas_detalhes.consultar_url_capa", return_value=URL_CAPA
    ) as consulta:
        resposta = client.get(f"/catalogo/musicbrainz/{MBID}/capa")

    assert resposta.status_code == 200
    assert resposta.json() == {"url": URL_CAPA}
    consulta.assert_called_once_with(MBID)


def test_rota_retorna_null_sem_capa():
    with patch("backend.app.rotas_detalhes.consultar_url_capa", return_value=None):
        resposta = client.get(f"/catalogo/musicbrainz/{MBID}/capa")

    assert resposta.status_code == 200
    assert resposta.json() == {"url": None}


def test_rota_rejeita_identificador_invalido():
    with patch("backend.app.rotas_detalhes.consultar_url_capa") as consulta:
        resposta = client.get("/catalogo/musicbrainz/id-invalido/capa")

    assert resposta.status_code == 422
    consulta.assert_not_called()


def test_rota_trata_falha_do_servico_externo():
    with patch(
        "backend.app.rotas_detalhes.consultar_url_capa",
        side_effect=httpx.ConnectError("indisponivel"),
    ):
        resposta = client.get(f"/catalogo/musicbrainz/{MBID}/capa")

    assert resposta.status_code == 502
    assert "Cover Art Archive" in resposta.json()["detail"]