
import pytest


# -----------------------------------------
# DADOS FICTICIOS DO MUSICBRAINZ
# -----------------------------------------


OBRAS_SIMULADAS = {
    "b1392450-e666-3926-a536-22c65f834433": {
        "id_musicbrainz": "b1392450-e666-3926-a536-22c65f834433",
        "titulo": "OK Computer",
        "artista": "Radiohead",
        "tipo": "Album",
        "data_lancamento": "1997-05-21",
    },
    "00000000-0000-0000-0000-000000000001": {
        "id_musicbrainz": "00000000-0000-0000-0000-000000000001",
        "titulo": "Disco A",
        "artista": "Artista A",
        "tipo": "Album",
        "data_lancamento": None,
    },
    "00000000-0000-0000-0000-000000000002": {
        "id_musicbrainz": "00000000-0000-0000-0000-000000000002",
        "titulo": "Disco B",
        "artista": "Artista B",
        "tipo": "Album",
        "data_lancamento": None,
    },
    "00000000-0000-0000-0000-000000000003": {
        "id_musicbrainz": "00000000-0000-0000-0000-000000000003",
        "titulo": "Disco C",
        "artista": "Artista C",
        "tipo": "Album",
        "data_lancamento": None,
    },
}


# -----------------------------------------
# SIMULACAO DO SERVICO EXTERNO
# -----------------------------------------


@pytest.fixture(autouse=True)
def simular_musicbrainz_no_catalogo(monkeypatch):
    """Evita consultas externas reais nos testes automatizados."""

    def consultar_obra_simulada(id_musicbrainz: str):
        dados = OBRAS_SIMULADAS.get(id_musicbrainz)

        if dados is None:
            return None

        return dados.copy()

    monkeypatch.setattr(
        "backend.app.catalogo.consultar_obra_por_id",
        consultar_obra_simulada,
    )
