from collections import OrderedDict

import httpx
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from backend.app import musicbrainz as mb
from backend.app import exploracao as ex
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
    monkeypatch.setattr(ex, "obter_popularidade", lambda *args: {})
    monkeypatch.setattr(ex, "obter_destaques", lambda *args: [])

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


def test_artista_popular_priorizado_sem_fixar_nome(cliente, monkeypatch):
    simular(monkeypatch, {
        "count": 2,
        "artists": [
            {"id": ARTISTA, "name": "Nirvana", "score": 100},
            {"id": FAIXA, "name": "Nirvana", "score": 95},
        ],
    })

    monkeypatch.setattr(
        ex, "obter_popularidade",
        lambda *args: {ARTISTA: 1, FAIXA: 50000},
    )

    c, _ = cliente
    r = c.get("/catalogo/explorar/busca?termo=Nirvana&categoria=artistas")

    assert r.status_code == 200
    assert r.json()["resultados"][0]["id_musicbrainz"] == FAIXA


def test_correspondencia_exata_supera_resultado_famoso(cliente, monkeypatch):
    simular(monkeypatch, {
        "count": 2,
        "artists": [
            {"id": ARTISTA, "name": "Nirvana", "score": 90},
            {"id": FAIXA, "name": "Outra Nirvana", "score": 100},
        ],
    })

    monkeypatch.setattr(
        ex, "obter_popularidade",
        lambda *args: {ARTISTA: 1, FAIXA: 1000000},
    )

    c, _ = cliente
    r = c.get("/catalogo/explorar/busca?termo=Nirvana&categoria=artistas")

    assert r.json()["resultados"][0]["id_musicbrainz"] == ARTISTA


def test_ranking_e_paginacao_usam_mesmos_candidatos(cliente, monkeypatch):
    chamadas = simular(monkeypatch, {
        "count": 3,
        "artists": [
            {"id": ARTISTA, "name": "Nirvana", "score": 100},
            {"id": FAIXA, "name": "Nirvana", "score": 100},
            {"id": ALBUM, "name": "Nirvana 2002", "score": 90},
        ],
    })

    monkeypatch.setattr(
        ex, "obter_popularidade",
        lambda *args: {ARTISTA: 10, FAIXA: 1000},
    )

    c, _ = cliente
    base = "/catalogo/explorar/busca?termo=Nirvana&categoria=artistas&limite=1"
    primeira = c.get(base).json()
    segunda = c.get(base + "&pagina=2").json()

    assert primeira["resultados"][0]["id_musicbrainz"] == FAIXA
    assert segunda["resultados"][0]["id_musicbrainz"] == ARTISTA
    assert primeira["tem_proxima"]
    assert len(chamadas) == 1
    assert chamadas[0][1]["limit"] == 60


def test_busca_aceita_correspondencia_aproximada(cliente, monkeypatch):
    chamadas = simular(monkeypatch, {
        "count": 1,
        "artists": [{"id": ARTISTA, "name": "Radiohead"}],
    })

    c, _ = cliente
    r = c.get("/catalogo/explorar/busca?termo=Radiohed&categoria=artistas")

    assert r.status_code == 200
    assert r.json()["resultados"][0]["titulo"] == "Radiohead"
    assert "artist:Radiohed~1" in chamadas[0][1]["query"]


def test_discografia_filtra_tipo_no_provedor(cliente, monkeypatch):
    chamadas = simular(monkeypatch, {
        "release-group-count": 1,
        "release-groups": [{
            **GRUPO, "secondary-types": ["Compilation"],
        }],
    })

    c, _ = cliente
    r = c.get(
        f"/catalogo/explorar/artistas/{ARTISTA}/discografia?tipo=compilation"
    )

    assert r.status_code == 200
    assert chamadas[0][1]["type"] == "compilation"
    assert r.json()["resultados"][0]["subtitulo"] == "Compilation"


def test_faixas_priorizam_edicao_com_metadados_completos(cliente, monkeypatch):
    simular(monkeypatch, {
        "releases": [
            {
                "id": EDICAO, "title": "Edicao incompleta",
                "date": "1991",
                "media": [{"tracks": [{"title": "[unknown]"}]}],
            },
            {
                "id": FAIXA, "title": "Edicao completa",
                "date": "1992",
                "media": [{"tracks": [{"title": "Come As You Are"}]}],
            },
        ],
    })

    c, _ = cliente
    r = c.get(f"/catalogo/explorar/albuns/{ALBUM}/faixas")

    assert r.status_code == 200
    assert r.json()["edicao_id"] == FAIXA
    assert r.json()["faixas"][0]["titulo"] == "Come As You Are"


def test_detalhe_album_inclui_mbid_do_artista(cliente, monkeypatch):
    simular(monkeypatch, {
        **GRUPO,
        "artist-credit": [{
            "name": "Nirvana",
            "artist": {"id": ARTISTA},
            "joinphrase": "",
        }],
    })

    c, _ = cliente
    r = c.get(f"/catalogo/musicbrainz/{ALBUM}")

    assert r.status_code == 200
    assert r.json()["creditos_artistas"] == [{
        "id_musicbrainz": ARTISTA,
        "nome": "Nirvana",
        "separador": "",
    }]


def test_busca_contextual_retorna_albuns_do_artista(cliente, monkeypatch):
    def destaques(categoria, artista_id):
        assert categoria == "albuns"
        assert artista_id == ARTISTA

        return [{
            "id_musicbrainz": ALBUM,
            "titulo": "Nevermind",
            "artista": "Nirvana",
            "tipo": "Album",
            "data": "1991",
            "ouvintes": 10000,
        }]

    monkeypatch.setattr(ex, "obter_destaques", destaques)

    c, _ = cliente
    r = c.get(
        f"/catalogo/explorar/busca?termo=Nirvana"
        f"&categoria=albuns&artista_id={ARTISTA}"
    )

    assert r.status_code == 200
    assert r.json()["resultados"][0]["id_musicbrainz"] == ALBUM


def test_fallback_contextual_preserva_mbid(cliente, monkeypatch):
    chamadas = simular(monkeypatch, {
        "count": 1,
        "release-groups": [GRUPO],
    })

    c, _ = cliente
    r = c.get(
        f"/catalogo/explorar/busca?termo=Nirvana"
        f"&categoria=albuns&artista_id={ARTISTA}"
    )

    assert r.status_code == 200
    assert r.json()["resultados"][0]["titulo"] == "Nevermind"
    assert f'arid:"{ARTISTA}"' in chamadas[0][1]["query"]


def test_faixas_populares_enriquecem_lancamentos(cliente, monkeypatch):
    monkeypatch.setattr(
        ex, "obter_destaques",
        lambda *args: [{
            "id_musicbrainz": FAIXA,
            "titulo": "Come As You Are",
            "artista": "Nirvana",
            "tipo": "Faixa",
            "ouvintes": 10000,
        }],
    )

    chamadas = simular(monkeypatch, {
        "recordings": [{
            "id": FAIXA,
            "title": "Come As You Are",
            "releases": [{
                "id": EDICAO,
                "title": "Nevermind",
                "release-group": {
                    "id": ALBUM, "title": "Nevermind",
                },
            }],
        }],
    })

    c, _ = cliente

    r = c.get(
        f"/catalogo/explorar/busca?termo=Nirvana"
        f"&categoria=faixas&artista_id={ARTISTA}"
    )

    assert r.status_code == 200

    item = r.json()["resultados"][0]

    assert item["id_musicbrainz"] == FAIXA
    assert item["relacionados"][0]["id_musicbrainz"] == ALBUM
    assert f'rid:"{FAIXA}"' in chamadas[0][1]["query"]


def test_contexto_rejeita_mbid_invalido(cliente):
    c, _ = cliente
    r = c.get(
        "/catalogo/explorar/busca?termo=Nirvana&artista_id=invalido"
    )
    assert r.status_code == 422


def test_previa_faixas_evitar_consulta_musicbrainz_extra(
    cliente, monkeypatch,
):
    monkeypatch.setattr(
        ex,
        "obter_destaques",
        lambda *args: [{
            "id_musicbrainz": FAIXA,
            "titulo": "Come As You Are",
            "artista": "Nirvana",
            "tipo": "Faixa",
            "ouvintes": 1000,
        }],
    )

    def consulta_inesperada(*args, **kwargs):
        pytest.fail("Previa nao deve consultar MusicBrainz.")

    monkeypatch.setattr(mb, "_consultar", consulta_inesperada)

    c, _ = cliente

    r = c.get(
        f"/catalogo/explorar/busca?termo=Nirvana"
        f"&categoria=faixas&artista_id={ARTISTA}&limite=3"
    )

    assert r.status_code == 200
    assert r.json()["resultados"][0]["titulo"] == "Come As You Are"
    assert r.json()["resultados"][0]["relacionados"] == []
