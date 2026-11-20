from collections import OrderedDict

import httpx
import pytest

from backend.app import musicbrainz as mb


def preparar(monkeypatch):
    instante = [100.0]

    monkeypatch.setattr(mb, "_cache", OrderedDict())
    monkeypatch.setattr(mb, "_agora", lambda: instante[0])
    monkeypatch.setattr(
        mb, "_dormir",
        lambda segundos: instante.__setitem__(
            0, instante[0] + segundos
        ),
    )
    monkeypatch.setattr(mb, "_proximo_inicio", 0.0)
    monkeypatch.setattr(mb, "_bloqueado_ate", 0.0)

    return instante


def test_cache_expirado_recupera_falha_503(monkeypatch):
    instante = preparar(monkeypatch)
    chamadas = []

    def simular(url, **kwargs):
        chamadas.append(url)
        status = 200 if len(chamadas) == 1 else 503

        return httpx.Response(
            status,
            request=httpx.Request("GET", url),
            json={"titulo": "Radiohead"} if status == 200 else {},
        )

    monkeypatch.setattr(mb.httpx, "get", simular)

    def consultar():
        return mb._consultar(
            "https://musicbrainz.org/ws/2/artist/",
            {"query": "radiohead"},
            "busca",
            5,
            lambda dados: dados["titulo"],
        )

    assert consultar() == "Radiohead"

    instante[0] += 6

    assert consultar() == "Radiohead"
    assert len(chamadas) == 3


def test_cache_obsoleto_tem_limite(monkeypatch):
    instante = preparar(monkeypatch)
    chamadas = []

    def simular(url, **kwargs):
        chamadas.append(url)
        status = 200 if len(chamadas) == 1 else 503

        return httpx.Response(
            status,
            request=httpx.Request("GET", url),
            json={"valor": 1} if status == 200 else {},
        )

    monkeypatch.setattr(mb.httpx, "get", simular)

    def consultar():
        return mb._consultar(
            "https://musicbrainz.org/ws/2/artist/",
            {"query": "teste"},
            "busca",
            5,
            lambda dados: dados["valor"],
        )

    assert consultar() == 1

    instante[0] += mb.TTL_CACHE_OBSOLETO + 10

    with pytest.raises(httpx.HTTPStatusError):
        consultar()
