from unittest.mock import patch

import httpx
import pytest

from backend.app import musicbrainz as mb

from backend.app.musicbrainz import (
    consultar_obra_por_id,
    pesquisar_obras,
)




@pytest.fixture(autouse=True)
def estado_isolado(monkeypatch):
    """Cada teste controla o relogio e tem seu proprio cache."""
    instante = [100.0]

    def dormir(segundos):
        instante[0] += segundos

    monkeypatch.setattr(mb, "_agora", lambda: instante[0])
    monkeypatch.setattr(mb, "_dormir", dormir)
    monkeypatch.setattr(mb, "_proximo_inicio", 0.0)
    monkeypatch.setattr(mb, "_bloqueado_ate", 0.0)
    monkeypatch.setattr(mb, "_cache", mb.OrderedDict())
    return instante


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

# -----------------------------------------
# F08.1 - RESILIENCIA E CACHE
# -----------------------------------------

MBID = "b1392450-e666-3926-a536-22c65f834433"


def resposta_http(status=200, dados=None, headers=None):
    return httpx.Response(
        status,
        json=dados,
        headers=headers,
        request=httpx.Request("GET", mb.URL_MUSICBRAINZ),
    )


def busca_ok():
    return resposta_http(dados={"release-groups": [
        {"id": MBID, "title": "OK Computer", "artist-credit": [{"name": "Radiohead"}]}
    ]})


def detalhe_ok():
    return resposta_http(dados={"id": MBID, "title": "OK Computer"})


def test_busca_repetida_utiliza_cache_e_isola_mutacao(estado_isolado):
    with patch("backend.app.musicbrainz.httpx.get", side_effect=lambda *a, **kw: busca_ok()) as get:
        primeira = pesquisar_obras("OK Computer")
        primeira[0]["titulo"] = "alteracao local"
        assert pesquisar_obras("OK Computer")[0]["titulo"] == "OK Computer"
        assert get.call_count == 1
        estado_isolado[0] += mb.TTL_BUSCA
        assert pesquisar_obras("OK Computer")[0]["titulo"] == "OK Computer"
        assert get.call_count == 2


def test_cache_distingue_filtros_da_busca():
    with patch("backend.app.musicbrainz.httpx.get", side_effect=lambda *a, **kw: busca_ok()) as get:
        pesquisar_obras("OK Computer")
        pesquisar_obras("OK Computer", "Radiohead")
        pesquisar_obras("OK Computer", "Radiohead")
        assert get.call_count == 2


def test_cache_detalhe_normaliza_mbid_e_expira(estado_isolado):
    with patch("backend.app.musicbrainz.httpx.get", side_effect=lambda *a, **kw: detalhe_ok()) as get:
        consultar_obra_por_id(MBID.upper())
        consultar_obra_por_id(MBID)
        assert get.call_count == 1
        estado_isolado[0] += mb.TTL_DETALHE
        consultar_obra_por_id(MBID)
        assert get.call_count == 2


def test_cache_tem_limite(monkeypatch):
    monkeypatch.setattr(mb, "MAX_CACHE", 2)
    with patch("backend.app.musicbrainz.httpx.get", side_effect=lambda *a, **kw: busca_ok()) as get:
        pesquisar_obras("A")
        pesquisar_obras("B")
        pesquisar_obras("A")  # A se torna a entrada mais recente.
        pesquisar_obras("C")
        pesquisar_obras("B")
        assert get.call_count == 4
        assert len(mb._cache) == 2


def test_intervalo_compartilhado_entre_busca_e_detalhe(estado_isolado):
    instantes = []

    def responder(url, **kwargs):
        instantes.append(estado_isolado[0])
        return detalhe_ok() if url.endswith(MBID) else busca_ok()

    with patch("backend.app.musicbrainz.httpx.get", side_effect=responder):
        pesquisar_obras("OK Computer")
        consultar_obra_por_id(MBID)
        pesquisar_obras("Loveless")
    assert len(instantes) == 3
    assert all(b - a >= mb.INTERVALO_REQUISICOES - 1e-8
               for a, b in zip(instantes, instantes[1:]))


@pytest.mark.parametrize("status", [429, 500, 502, 503, 504])
def test_recupera_erro_transitorio_e_respeita_intervalo(status, estado_isolado):
    inicio = estado_isolado[0]
    with patch("backend.app.musicbrainz.httpx.get",
               side_effect=[resposta_http(status), busca_ok()]) as get:
        assert pesquisar_obras("OK Computer")[0]["titulo"] == "OK Computer"
        assert get.call_count == 2
        assert estado_isolado[0] - inicio >= 2.0


def test_timeout_tem_uma_nova_tentativa():
    with patch("backend.app.musicbrainz.httpx.get",
               side_effect=[httpx.ReadTimeout("timeout simulado"), detalhe_ok()]) as get:
        assert consultar_obra_por_id(MBID)["titulo"] == "OK Computer"
        assert get.call_count == 2


def test_retry_after_curto_e_respeitado(estado_isolado):
    inicio = estado_isolado[0]
    with patch("backend.app.musicbrainz.httpx.get",
               side_effect=[resposta_http(503, headers={"Retry-After": "3"}), busca_ok()]) as get:
        pesquisar_obras("OK Computer")
        assert get.call_count == 2
        assert estado_isolado[0] - inicio >= 3.0


def test_retry_after_longo_evitar_novas_requisicoes(estado_isolado):
    with patch("backend.app.musicbrainz.httpx.get",
               side_effect=[resposta_http(429, headers={"Retry-After": "60"}), busca_ok()]) as get:
        with pytest.raises(httpx.HTTPStatusError):
            pesquisar_obras("OK Computer")
        with pytest.raises(httpx.RequestError):
            pesquisar_obras("Loveless")
        assert get.call_count == 1
        estado_isolado[0] += 60
        pesquisar_obras("OK Computer")
        assert get.call_count == 2


def test_falha_definitiva_nao_e_armazenada():
    with patch("backend.app.musicbrainz.httpx.get",
               side_effect=[resposta_http(503), resposta_http(503), busca_ok()]) as get:
        with pytest.raises(httpx.HTTPStatusError):
            pesquisar_obras("OK Computer")
        assert get.call_count == 2
        assert pesquisar_obras("OK Computer")[0]["titulo"] == "OK Computer"
        assert get.call_count == 3


def test_erro_permanente_nao_tem_retry():
    with patch("backend.app.musicbrainz.httpx.get", return_value=resposta_http(400)) as get:
        with pytest.raises(httpx.HTTPStatusError):
            pesquisar_obras("OK Computer")
        assert get.call_count == 1


def test_detalhe_404_nao_tem_retry():
    with patch("backend.app.musicbrainz.httpx.get", return_value=resposta_http(404)) as get:
        assert consultar_obra_por_id(MBID) is None
        assert get.call_count == 1


def test_resposta_invalida_nao_vira_cache_nem_lista_vazia():
    with patch("backend.app.musicbrainz.httpx.get",
               side_effect=[resposta_http(dados={"unexpected": True}), busca_ok()]) as get:
        with pytest.raises(httpx.DecodingError):
            pesquisar_obras("OK Computer")
        assert pesquisar_obras("OK Computer")[0]["titulo"] == "OK Computer"
        assert get.call_count == 2


def test_resposta_sem_resultados_e_valida():
    with patch("backend.app.musicbrainz.httpx.get",
               return_value=resposta_http(dados={"release-groups": []})) as get:
        assert pesquisar_obras("album inexistente") == []
        assert pesquisar_obras("album inexistente") == []
        assert get.call_count == 1


def test_log_registra_status_real_sem_termo(caplog):
    with patch("backend.app.musicbrainz.httpx.get",
               side_effect=[resposta_http(503), busca_ok()]):
        pesquisar_obras("termo privado")
    assert "MusicBrainz busca: HTTP 503" in caplog.text
    assert "termo privado" not in caplog.text


def test_consultas_simultaneas_identicas_reutilizam_cache():
    from concurrent.futures import ThreadPoolExecutor

    with patch("backend.app.musicbrainz.httpx.get",
               side_effect=lambda *a, **kw: busca_ok()) as get:
        with ThreadPoolExecutor(max_workers=4) as executor:
            resultados = list(executor.map(pesquisar_obras, ["OK Computer"] * 4))
        assert all(r[0]["titulo"] == "OK Computer" for r in resultados)
        assert get.call_count == 1


def test_cache_disponivel_mesmo_em_cooldown():
    with patch("backend.app.musicbrainz.httpx.get",
               side_effect=[busca_ok(), resposta_http(503, headers={"Retry-After": "60"})]) as get:
        pesquisar_obras("OK Computer")
        with pytest.raises(httpx.HTTPStatusError):
            pesquisar_obras("Loveless")
        assert pesquisar_obras("OK Computer")[0]["titulo"] == "OK Computer"
        assert get.call_count == 2