from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from backend.app.database import obter_sessao
from backend.app.main import app
from backend.app.models import Avaliacao, Base, Escuta, Obra, Review, Usuario


@pytest.fixture
def ambiente():
    motor = create_engine("sqlite+pysqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(motor)

    def sessao_teste():
        with Session(motor) as sessao:
            yield sessao

    app.dependency_overrides[obter_sessao] = sessao_teste
    try:
        with TestClient(app) as cliente:
            yield cliente, motor
    finally:
        app.dependency_overrides.pop(obter_sessao, None)
        motor.dispose()


def popular(motor):
    with Session(motor) as s:
        a = Usuario(username="autor_a", nome_exibicao="Autor A", email="a@example.com", senha_hash="ficticio")
        b = Usuario(username="autor_b", nome_exibicao="Autor B", email="b@example.com", senha_hash="ficticio")
        obra = Obra(id_musicbrainz="00000000-0000-0000-0000-000000000001", titulo="Disco A", artista="Artista A", tipo="Album")
        s.add_all([a, b, obra]); s.flush()
        data = datetime(2026, 1, 1, tzinfo=timezone.utc)
        primeira = Review(usuario_id=a.id, obra_id=obra.id, texto="Primeira", criada_em=data)
        s.add(primeira); s.flush()
        segunda = Review(usuario_id=b.id, obra_id=obra.id, texto="Segunda", criada_em=data)
        s.add_all([segunda, Avaliacao(usuario_id=a.id, obra_id=obra.id, nota_passos=9)])
        s.commit()
        return primeira.id, segunda.id


def test_feed_vazio(ambiente):
    cliente, _ = ambiente
    r = cliente.get("/social/reviews")
    assert r.status_code == 200
    assert r.json() == {"pagina": 1, "por_pagina": 12, "tem_proxima": False, "resultados": []}


def test_feed_publico_nota_do_autor_e_campos_seguros(ambiente):
    cliente, motor = ambiente
    primeira, segunda = popular(motor)
    r = cliente.get("/social/reviews")
    assert r.status_code == 200
    itens = r.json()["resultados"]
    assert [i["id"] for i in itens] == [segunda, primeira]
    assert [(i["username"], i["nota"]) for i in itens] == [("autor_b", None), ("autor_a", 4.5)]
    assert itens[1]["nome_exibicao"] == "Autor A"
    assert itens[1]["titulo"] == "Disco A"
    assert set(itens[1]) == {"id", "username", "nome_exibicao", "id_musicbrainz", "titulo", "artista", "texto", "nota", "criada_em", "atualizada_em"}
    with Session(motor) as s:
        assert s.scalar(select(func.count(Escuta.id))) == 0
        assert s.scalar(select(func.count(Review.id))) == 2


def test_paginacao_e_desempate(ambiente):
    cliente, motor = ambiente
    primeira, segunda = popular(motor)
    p1 = cliente.get("/social/reviews?pagina=1&por_pagina=1").json()
    p2 = cliente.get("/social/reviews?pagina=2&por_pagina=1").json()
    p3 = cliente.get("/social/reviews?pagina=3&por_pagina=1").json()
    assert p1["tem_proxima"] and p1["resultados"][0]["id"] == segunda
    assert not p2["tem_proxima"] and p2["resultados"][0]["id"] == primeira
    assert not p3["tem_proxima"] and p3["resultados"] == []


def test_edicao_e_exclusao_refletidas_no_feed(ambiente):
    cliente, motor = ambiente
    primeira, segunda = popular(motor)
    with Session(motor) as s:
        review = s.get(Review, primeira)
        review.texto = "Texto atualizado"
        s.delete(s.get(Review, segunda))
        s.commit()
    itens = cliente.get("/social/reviews").json()["resultados"]
    assert len(itens) == 1 and itens[0]["texto"] == "Texto atualizado"


@pytest.mark.parametrize("query", ["pagina=0", "pagina=10001", "por_pagina=0", "por_pagina=51", "pagina=abc"])
def test_rejeita_paginacao_invalida(ambiente, query):
    cliente, _ = ambiente
    assert cliente.get(f"/social/reviews?{query}").status_code == 422