from unittest.mock import patch

import httpx
from fastapi.testclient import TestClient

from backend.app.main import app

client = TestClient(app)
MBID = "b1392450-e666-3926-a536-22c65f834433"


def test_detalhe_por_mbid_retorna_metadados():
    obra = {
        "id_musicbrainz": MBID,
        "titulo": "OK Computer",
        "artista": "Radiohead",
        "tipo": "Album",
        "data_lancamento": "1997-05-21",
    }
    with patch(
        "backend.app.rotas_detalhes.consultar_obra_por_id", return_value=obra
    ) as consulta:
        resposta = client.get(f"/catalogo/musicbrainz/{MBID}")

    assert resposta.status_code == 200
    assert resposta.json() == obra
    consulta.assert_called_once_with(MBID)


def test_detalhe_rejeita_mbid_invalido():
    with patch("backend.app.rotas_detalhes.consultar_obra_por_id") as consulta:
        resposta = client.get("/catalogo/musicbrainz/id-invalido")

    assert resposta.status_code == 422
    consulta.assert_not_called()


def test_detalhe_retorna_404_se_obra_nao_existe():
    with patch(
        "backend.app.rotas_detalhes.consultar_obra_por_id", return_value=None
    ):
        resposta = client.get(f"/catalogo/musicbrainz/{MBID}")

    assert resposta.status_code == 404


def test_detalhe_trata_falha_externa_com_502():
    with patch(
        "backend.app.rotas_detalhes.consultar_obra_por_id",
        side_effect=httpx.ConnectError("indisponivel"),
    ):
        resposta = client.get(f"/catalogo/musicbrainz/{MBID}")

    assert resposta.status_code == 502
    assert "MusicBrainz" in resposta.json()["detail"]