"""Entrega 03: paginacao e enriquecimento sem tocar no banco real."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from backend.app.auth import criar_token
from backend.app.database import obter_sessao
from backend.app.main import app
from backend.app.models import (
    Avaliacao,
    Base,
    Escuta,
    Favorito,
    ItemLista,
    ListaMusical,
    Obra,
    ObraOuvida,
    Review,
    Usuario,
)


@pytest.fixture
def ambiente(monkeypatch):
    monkeypatch.setenv(
        "JWT_SECRET", "chave-ficticia-exclusiva-para-testes-123456789"
    )
    motor = create_engine(
        "sqlite+pysqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(motor)

    with Session(motor) as sessao:
        usuario = Usuario(
            username="usuario_paginacao",
            nome_exibicao="Teste",
            email="paginacao@example.com",
            senha_hash="hash-ficticio",
        )
        obra1 = Obra(
            id_musicbrainz="00000000-0000-0000-0000-000000000011",
            titulo="Disco Um", artista="Artista Um", tipo="Album",
        )
        obra2 = Obra(
            id_musicbrainz="00000000-0000-0000-0000-000000000012",
            titulo="Disco Dois", artista="Artista Dois", tipo="Album",
        )
        sessao.add_all([usuario, obra1, obra2])
        sessao.flush()
        usuario_id = usuario.id
        ids = [obra1.id, obra2.id]
        lista = ListaMusical(usuario_id=usuario_id, titulo="Minha lista", publica=True)
        sessao.add(lista)
        sessao.flush()
        lista_id = lista.id
        for posicao, obra_id in enumerate(ids, start=1):
            sessao.add_all([
                Favorito(usuario_id=usuario_id, obra_id=obra_id),
                ObraOuvida(usuario_id=usuario_id, obra_id=obra_id),
                Escuta(usuario_id=usuario_id, obra_id=obra_id),
                Avaliacao(usuario_id=usuario_id, obra_id=obra_id, nota_passos=8),
                Review(usuario_id=usuario_id, obra_id=obra_id, texto=f"Review {posicao}"),
                ItemLista(lista_id=lista_id, obra_id=obra_id, posicao=posicao),
            ])
        sessao.commit()

    def sessao_teste():
        with Session(motor) as sessao:
            yield sessao

    app.dependency_overrides[obter_sessao] = sessao_teste
    token = criar_token(usuario_id)
    headers = {"Authorization": f"Bearer {token}"}
    try:
        with TestClient(app) as cliente:
            yield cliente, headers, lista_id, ids
    finally:
        app.dependency_overrides.pop(obter_sessao, None)
        motor.dispose()


def test_catalogo_paginado_preserva_formato(ambiente):
    cliente, _, _, ids = ambiente
    primeira = cliente.get("/catalogo/obras", params={"pagina": 1, "por_pagina": 1})
    segunda = cliente.get("/catalogo/obras", params={"pagina": 2, "por_pagina": 1})
    vazia = cliente.get("/catalogo/obras", params={"pagina": 3, "por_pagina": 1})

    assert primeira.status_code == segunda.status_code == vazia.status_code == 200
    assert [item["id"] for item in primeira.json()["resultados"]] == [ids[0]]
    assert [item["id"] for item in segunda.json()["resultados"]] == [ids[1]]
    assert vazia.json() == {"resultados": []}


def test_favoritos_com_metadados_e_paginas_distintas(ambiente):
    cliente, headers, _, ids = ambiente
    primeira = cliente.get(
        "/biblioteca/favoritos", params={"pagina": 1, "por_pagina": 1}, headers=headers
    )
    segunda = cliente.get(
        "/biblioteca/favoritos", params={"pagina": 2, "por_pagina": 1}, headers=headers
    )
    assert primeira.status_code == segunda.status_code == 200
    a, b = primeira.json(), segunda.json()
    assert len(a) == len(b) == 1
    assert {a[0]["obra_id"], b[0]["obra_id"]} == set(ids)
    assert a[0]["titulo"] in {"Disco Um", "Disco Dois"}
    assert b[0]["artista"] in {"Artista Um", "Artista Dois"}
    assert a[0]["id_musicbrainz"] is not None
    assert a[0]["adicionado_em"] is not None


@pytest.mark.parametrize(
    "rota, campo",
    [
        ("/interacoes/escutas", "ouvida_em"),
        ("/interacoes/obras-ouvidas", "marcada_em"),
        ("/interacoes/avaliacoes", "nota"),
        ("/interacoes/reviews", "texto"),
    ],
)
def test_interacoes_trazem_obra_sem_perder_campos(ambiente, rota, campo):
    cliente, headers, _, _ = ambiente
    resposta = cliente.get(rota, params={"por_pagina": 1}, headers=headers)
    assert resposta.status_code == 200
    assert len(resposta.json()) == 1
    item = resposta.json()[0]
    assert item["titulo"] in {"Disco Um", "Disco Dois"}
    assert item["id_musicbrainz"] is not None
    assert item[campo] is not None


def test_itens_publicos_paginados_com_metadados(ambiente):
    cliente, _, lista_id, ids = ambiente
    pagina = cliente.get(
        f"/listas/{lista_id}/itens", params={"pagina": 2, "por_pagina": 1}
    )
    assert pagina.status_code == 200
    assert len(pagina.json()) == 1
    assert pagina.json()[0]["posicao"] == 2
    assert pagina.json()[0]["obra_id"] == ids[1]
    assert pagina.json()[0]["titulo"] == "Disco Dois"


def test_paginacao_invalida_retorna_422(ambiente):
    cliente, headers, _, _ = ambiente
    for parametros in ({"pagina": 0}, {"por_pagina": 0}, {"por_pagina": 101}):
        resposta = cliente.get("/biblioteca/favoritos", params=parametros, headers=headers)
        assert resposta.status_code == 422


def test_reviews_publicas_paginadas_e_listas_privadas(ambiente):
    cliente, headers, lista_id, ids = ambiente
    reviews = cliente.get(
        f"/interacoes/reviews/obra/{ids[0]}", params={"por_pagina": 1}
    )
    assert reviews.status_code == 200
    assert reviews.json()[0]["titulo"] == "Disco Um"
    minhas = cliente.get("/listas/minhas", params={"pagina": 1, "por_pagina": 1}, headers=headers)
    assert minhas.status_code == 200
    assert minhas.json()[0]["id"] == lista_id
