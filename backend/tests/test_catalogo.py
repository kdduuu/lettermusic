
from unittest.mock import patch

from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)


def test_busca_retorna_obras():
    obras_simuladas = [
        {
            "id_musicbrainz": "exemplo-123",
            "titulo": "OK Computer",
            "tipo": "Album",
            "data_lancamento": "1997-05-21"
        }
    ]

    with patch(
        "backend.app.main.pesquisar_obras",
        return_value=obras_simuladas
    ):
        resposta = client.get(
            "/catalogo/buscar",
            params={"termo": "OK Computer"}
        )

    assert resposta.status_code == 200
    assert resposta.json() == {"resultados": obras_simuladas}
