from collections import OrderedDict

import httpx
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from backend.app import musicbrainz as mb
from backend.app.database import obter_sessao
from backend.app.main import app
from backend.app.models import Base, Obra

ALBUM = "00000000-0000-0000-0000-000000000001"
ARTISTA = "00000000-0000-0000-0000-000000000002"
FAIXA = "00000000-0000-0000-0000-000000000003"
EDICAO = "00000000-0000-0000-0000-000000000004"

GRUPO = {
    "id": ALBUM, "title": "Nevermind",
    "artist-credit": [{"name": "Nirvana"}],
    "primary-type": "Album",
}


@pytest.fixture
def cliente(monkeypatch):
    instante = [100.0]
    monkeypatch.setattr(mb, "_cache", OrderedDict())
    monkeypatch.setattr(mb, "_agora", lambda: instante[0])
    monkeypatch.setattr(mb, "_dormir", lambda s: instante.__setitem__(0, instante[0] + s))
    monkeypatch.setattr(mb, "_proximo_inicio", 0.0)
    monkeypatch.setattr(mb, "_bloqueado_ate", 0.0)

    def bloquear_rede(*args, **kwargs):
        pytest.fail("Consulta externa nao simulada.")

    monkeypatch.setattr(mb.httpx, "get", bloquear_rede)

    motor = create_engine(
        "sqlite+pysqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(motor)

    def sessao():
        with Session(motor) as s:
            yield s

    app.dependency_overrides[obter_sessao] = sessao
    try:
        with TestClient(app) as c:
            yield c, motor
    finally:
        app.dependency_overrides.pop(obter_sessao, None)
        motor.dispose()


def simular(monkeypatch, dados, status=200):
    chamadas = []

    def resposta(url, **kwargs):
        chamadas.append((url, kwargs["params"]))
        return httpx.Response(
            status, json=dados,
            request=httpx.Request("GET", url),
        )

    monkeypatch.setattr(mb.httpx, "get", resposta)
    return chamadas


def test_busca_por_artista_e_titulo(cliente, monkeypatch):
    chamadas = simular(monkeypatch, {
        "count": 1, "release-groups": [GRUPO],
    })

    c, _ = cliente
    r = c.get("/catalogo/explorar/busca?termo=Nirvana+Nevermind")
    assert r.status_code == 200
    assert r.json()["resultados"][0]["titulo"] == "Nevermind"
    assert 'artistname:"Nirvana"' in chamadas[0][1]["query"]
    assert 'releasegroup:"Nevermind"' in chamadas[0][1]["query"]
    assert not r.json()["tem_proxima"]


def test_pesquisa_reutiliza_cache(cliente, monkeypatch):
    chamadas = simular(monkeypatch, {
        "count": 1, "release-groups": [GRUPO],
    })

    c, _ = cliente
    caminho = "/catalogo/explorar/busca?termo=Nirvana"
    assert c.get(caminho).status_code == 200
    assert c.get(caminho).status_code == 200
    assert len(chamadas) == 1


def test_artista(cliente, monkeypatch):
    simular(monkeypatch, {"id": ARTISTA, "name": "Nirvana"})
    c, _ = cliente
    r = c.get(f"/catalogo/explorar/artistas/{ARTISTA}")
    assert r.status_code == 200
    assert r.json()["titulo"] == "Nirvana"


def test_artista_inexistente(cliente, monkeypatch):
    simular(monkeypatch, {}, 404)
    c, _ = cliente
    assert c.get(f"/catalogo/explorar/artistas/{ARTISTA}").status_code == 404


def test_discografia_paginada(cliente, monkeypatch):
    chamadas = simular(monkeypatch, {
        "release-group-count": 30, "release-groups": [GRUPO],
    })

    c, _ = cliente
    r = c.get(f"/catalogo/explorar/artistas/{ARTISTA}/discografia?pagina=2")
    assert r.status_code == 200
    assert r.json()["tem_proxima"]
    assert chamadas[0][1]["artist"] == ARTISTA
    assert chamadas[0][1]["offset"] == 12


def test_faixa_aponta_para_grupo_e_nao_edicao(cliente, monkeypatch):
    simular(monkeypatch, {
        "count": 1,
        "recordings": [{
            "id": FAIXA, "title": "Come As You Are",
            "releases": [{
                "id": EDICAO, "title": "Nevermind",
                "release-group": {"id": ALBUM},
            }],
        }],
    })

    c, _ = cliente
    r = c.get("/catalogo/explorar/busca?termo=Come+As+You+Are&categoria=faixas")
    assert r.status_code == 200
    assert r.json()["resultados"][0]["relacionados"][0]["id_musicbrainz"] == ALBUM


def test_faixas_identificam_edicao(cliente, monkeypatch):
    simular(monkeypatch, {
        "releases": [{
            "id": EDICAO, "title": "Nevermind", "date": "1991",
            "media": [{"tracks": [{
                "number": "1", "title": "Smells Like Teen Spirit",
                "length": 301000,
            }]}],
        }],
    })

    c, _ = cliente
    r = c.get(f"/catalogo/explorar/albuns/{ALBUM}/faixas")
    assert r.status_code == 200
    assert r.json()["edicao_id"] == EDICAO
    assert r.json()["faixas"][0]["duracao_ms"] == 301000


def test_falha_externa_controlada(cliente, monkeypatch):
    simular(monkeypatch, {}, 503)
    c, _ = cliente
    assert c.get("/catalogo/explorar/busca?termo=Nirvana").status_code == 502


@pytest.mark.parametrize("query", [
    "termo=Nirvana&categoria=invalida",
    "termo=Nirvana&pagina=0",
    "termo=Nirvana&limite=25",
    "termo=++",
])
def test_rejeita_parametros_invalidos(cliente, query):
    c, _ = cliente
    assert c.get(f"/catalogo/explorar/busca?{query}").status_code == 422


def test_catalogo_local_filtra_sem_consultar_api(cliente):
    c, motor = cliente
    with Session(motor) as s:
        s.add(Obra(
            id_musicbrainz=ALBUM, titulo="Nevermind",
            artista="Nirvana", tipo="Album",
        ))
        s.commit()

    r = c.get("/catalogo/explorar/local?termo=nirvana&tipo=Album")
    assert r.status_code == 200
    assert r.json()["resultados"][0]["titulo"] == "Nevermind"
    assert not r.json()["tem_proxima"]
