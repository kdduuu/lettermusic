from collections import OrderedDict

import httpx
import pytest

from backend.app import popularidade as pop

A = "00000000-0000-0000-0000-000000000001"
B = "00000000-0000-0000-0000-000000000002"


@pytest.fixture(autouse=True)
def estado_isolado(monkeypatch):
    monkeypatch.setattr(pop, "_cache", OrderedDict())
    monkeypatch.setattr(pop, "_bloqueado_ate", 0.0)
    monkeypatch.setattr(pop, "_proximo_inicio", 0.0)
    monkeypatch.setenv("LISTENBRAINZ_TOKEN", "token-de-teste")
    monkeypatch.setenv("LISTENBRAINZ_ENABLED", "true")

    instante = [100.0]
    monkeypatch.setattr(pop, "_agora", lambda: instante[0])
    monkeypatch.setattr(
        pop, "_dormir",
        lambda segundos: instante.__setitem__(0, instante[0] + segundos),
    )


def test_popularidade_consulta_em_lote_e_reutiliza_cache(monkeypatch):
    chamadas = []

    def post(url, **kwargs):
        chamadas.append(kwargs["json"])
        return httpx.Response(
            200,
            request=httpx.Request("POST", url),
            json=[
                {"artist_mbid": A, "total_user_count": 100},
                {"artist_mbid": B, "total_user_count": None},
            ],
        )

    monkeypatch.setattr(pop.httpx, "post", post)

    assert pop.obter_popularidade("artistas", [A, B]) == {A: 100}
    assert pop.obter_popularidade("artistas", [B, A]) == {A: 100}
    assert chamadas == [{"artist_mbids": [A, B]}]


def test_popularidade_indisponivel_nao_bloqueia_aplicacao(monkeypatch):
    chamadas = []

    def post(url, **kwargs):
        chamadas.append(url)
        raise httpx.ConnectError("Provedor indisponivel")

    monkeypatch.setattr(pop.httpx, "post", post)

    assert pop.obter_popularidade("artistas", [A, B]) == {}
    assert pop.obter_popularidade("albuns", [A, B]) == {}
    assert len(chamadas) == 1


def test_sem_token_nao_realiza_requisicao(monkeypatch):
    monkeypatch.delenv("LISTENBRAINZ_TOKEN", raising=False)

    def bloquear(*args, **kwargs):
        pytest.fail("Nao deveria consultar sem token")

    monkeypatch.setattr(pop.httpx, "post", bloquear)
    monkeypatch.setattr(pop.httpx, "get", bloquear)

    assert pop.obter_popularidade("artistas", [A, B]) == {}
    assert pop.obter_destaques("albuns", A) == []


def test_integracao_pode_ser_desativada(monkeypatch):
    monkeypatch.setenv("LISTENBRAINZ_ENABLED", "false")

    def bloquear(*args, **kwargs):
        pytest.fail("Integracao desativada")

    monkeypatch.setattr(pop.httpx, "get", bloquear)

    assert pop.obter_destaques("albuns", A) == []


def test_destaques_usam_release_group_e_autenticacao(monkeypatch):
    chamadas = []

    def get(url, **kwargs):
        chamadas.append(url)

        assert kwargs["headers"]["Authorization"] == "Token token-de-teste"

        return httpx.Response(
            200,
            request=httpx.Request("GET", url),
            json=[
                {
                    "release_group_mbid": A,
                    "release_group": {
                        "name": "Album A", "type": "Album",
                        "caa_release_mbid": B,
                    },
                    "artist": {"name": "Artista"},
                    "total_user_count": 100,
                },
                {
                    "release_group_mbid": B,
                    "release_group": {
                        "name": "Album B", "type": "Album",
                    },
                    "artist": {"name": "Artista"},
                    "total_user_count": 500,
                },
            ],
        )

    monkeypatch.setattr(pop.httpx, "get", get)

    itens = pop.obter_destaques("albuns", A)

    assert [item["id_musicbrainz"] for item in itens] == [B, A]
    assert itens[1]["titulo"] == "Album A"
    assert pop.obter_destaques("albuns", A) == itens
    assert len(chamadas) == 1


def test_intervalo_compartilhado_entre_get_e_post(monkeypatch):
    instantes = []

    def responder(url, **kwargs):
        instantes.append(pop._agora())
        return httpx.Response(
            200, json=[],
            request=httpx.Request("GET", url),
        )

    monkeypatch.setattr(pop.httpx, "get", responder)
    monkeypatch.setattr(pop.httpx, "post", responder)

    pop.obter_popularidade("artistas", [A, B])
    pop.obter_destaques("albuns", A)
    pop.obter_destaques("faixas", A)

    assert len(instantes) == 3
    assert all(
        b - a >= pop.INTERVALO - 1e-8
        for a, b in zip(instantes, instantes[1:])
    )


def test_429_interrompe_consultas_ate_reset(monkeypatch):
    chamadas = []

    def responder(url, **kwargs):
        chamadas.append(url)

        return httpx.Response(
            429, json={},
            headers={"X-RateLimit-Reset-In": "120"},
            request=httpx.Request("GET", url),
        )

    monkeypatch.setattr(pop.httpx, "get", responder)
    monkeypatch.setattr(pop.httpx, "post", responder)

    assert pop.obter_destaques("albuns", A) == []
    assert pop.obter_popularidade("artistas", [A, B]) == {}
    assert len(chamadas) == 1
    assert pop._bloqueado_ate >= pop._agora() + 120
