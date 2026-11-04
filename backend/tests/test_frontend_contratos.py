"""Contrato consumido pelo navegador e protecao de origens da API."""

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from pydantic import ValidationError

from backend.app.cors import configurar_cors
from backend.app.schemas_interacoes import (
    AdicionarItemBibliotecaEntrada,
    MetadadosObraOficial,
    ObraInteracao,
)


MBID = "b1392450-e666-3926-a536-22c65f834433"


@pytest.fixture
def app_cors(monkeypatch):
    monkeypatch.setenv(
        "CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173"
    )
    app = FastAPI()
    configurar_cors(app)

    @app.get("/teste")
    def verificar():
        return {"ok": True}

    return app


def test_cors_aceita_preflight_do_frontend(app_cors):
    with TestClient(app_cors) as cliente:
        resposta = cliente.options(
            "/teste",
            headers={
                "Origin": "http://localhost:5173",
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "authorization,content-type",
            },
        )
    assert resposta.status_code == 200
    assert resposta.headers["access-control-allow-origin"] == "http://localhost:5173"


def test_cors_rejeita_origem_estranha(app_cors):
    with TestClient(app_cors) as cliente:
        resposta = cliente.options(
            "/teste",
            headers={
                "Origin": "https://origem-nao-autorizada.example",
                "Access-Control-Request-Method": "POST",
            },
        )
    assert resposta.status_code == 400
    assert "access-control-allow-origin" not in resposta.headers


def test_cors_permite_get_da_origem_correta(app_cors):
    with TestClient(app_cors) as cliente:
        resposta = cliente.get(
            "/teste", headers={"Origin": "http://127.0.0.1:5173"}
        )
    assert resposta.status_code == 200
    assert resposta.headers["access-control-allow-origin"] == "http://127.0.0.1:5173"


def test_cors_nao_aceita_curinga(monkeypatch):
    monkeypatch.setenv("CORS_ORIGINS", "*")
    with pytest.raises(ValueError, match="Origem CORS invalida"):
        configurar_cors(FastAPI())


def test_contrato_aceita_apenas_id_musicbrainz():
    entrada = AdicionarItemBibliotecaEntrada(
        obra={"id_musicbrainz": MBID}
    )
    assert entrada.obra.id_musicbrainz == MBID


def test_contrato_antigo_nao_envia_metadados_ao_backend():
    entrada = ObraInteracao.model_validate(
        {
            "id_musicbrainz": MBID,
            "titulo": "Titulo falso",
            "artista": "Artista falso",
        }
    )
    assert entrada.model_dump() == {"id_musicbrainz": MBID}


def test_metadados_oficiais_exigem_titulo():
    with pytest.raises(ValidationError):
        MetadadosObraOficial.model_validate(
            {"id_musicbrainz": MBID}
        )
