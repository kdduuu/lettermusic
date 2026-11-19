from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event, select, func
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from backend.app.comunidade import consultar_comunidade
from backend.app.database import obter_sessao
from backend.app.main import app
from backend.app.models import Avaliacao, Base, Escuta, Favorito, ItemLista, ListaMusical, Obra, QueroOuvir, Review, Usuario


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
    agora = datetime.now(timezone.utc)
    with Session(motor) as s:
        a = Usuario(username="autor_a", nome_exibicao="Autor A", email="a@example.com", senha_hash="teste")
        b = Usuario(username="autor_b", nome_exibicao="Autor B", email="b@example.com", senha_hash="teste")
        c = Usuario(username="autor_c", nome_exibicao="Autor C", email="c@example.com", senha_hash="teste")
        obra_a = Obra(id_musicbrainz="00000000-0000-0000-0000-000000000001", titulo="Disco A", artista="Artista A", tipo="Album")
        obra_b = Obra(id_musicbrainz="00000000-0000-0000-0000-000000000002", titulo="Disco B", artista="Artista B", tipo="Album")
        obra_c = Obra(id_musicbrainz="00000000-0000-0000-0000-000000000003", titulo="Disco C", artista=None, tipo="Album")
        s.add_all([a, b, c, obra_a, obra_b, obra_c]); s.flush()
        privada = ListaMusical(usuario_id=c.id, titulo="Segredo", descricao="Nunca publicar", publica=False, criada_em=agora - timedelta(hours=1))
        publica = ListaMusical(usuario_id=a.id, titulo="Lista pública", publica=True, criada_em=agora - timedelta(days=1))
        s.add_all([privada, publica]); s.flush()
        s.add_all([
            Review(usuario_id=a.id, obra_id=obra_a.id, texto="Review A", criada_em=agora - timedelta(days=2)),
            Avaliacao(usuario_id=a.id, obra_id=obra_a.id, nota_passos=9, criada_em=agora - timedelta(days=3)),
            Avaliacao(usuario_id=b.id, obra_id=obra_a.id, nota_passos=8, criada_em=agora - timedelta(days=4)),
            Review(usuario_id=b.id, obra_id=obra_b.id, texto="Review antiga", criada_em=agora - timedelta(days=31), atualizada_em=agora - timedelta(hours=2)),
            Escuta(usuario_id=c.id, obra_id=obra_c.id), Favorito(usuario_id=c.id, obra_id=obra_c.id), QueroOuvir(usuario_id=c.id, obra_id=obra_c.id),
            ItemLista(lista_id=privada.id, obra_id=obra_c.id, posicao=1),
        ])
        s.commit()
        return agora, publica.id, privada.id


def test_comunidade_vazia_e_publica(ambiente):
    cliente, _ = ambiente
    r = cliente.get("/social/comunidade")
    assert r.status_code == 200
    assert r.json() == {"janela_dias": 30, "atividades": [], "membros_ativos": [], "em_alta": []}


def test_feed_cronologico_e_tipos(ambiente):
    cliente, motor = ambiente
    _, publica, _ = popular(motor)
    r = cliente.get("/social/comunidade")
    assert r.status_code == 200
    itens = r.json()["atividades"]
    assert [i["tipo"] for i in itens] == ["lista", "review", "avaliacao", "avaliacao", "review"]
    assert itens[0]["id"] == publica and itens[0]["titulo"] == "Lista pública"
    assert itens[1]["texto"] == "Review A" and itens[1]["titulo"] == "Disco A"
    assert itens[2]["nota"] == 4.5
    assert itens[-1]["texto"] == "Review antiga"  # Edicao nao vira atividade nova.


def test_membros_e_em_alta_apenas_janela_recente(ambiente):
    cliente, motor = ambiente
    popular(motor)
    dados = cliente.get("/social/comunidade").json()
    assert dados["janela_dias"] == 30
    assert [(i["username"], i["contribuicoes"]) for i in dados["membros_ativos"]] == [("autor_a", 3), ("autor_b", 1)]
    assert [(i["titulo"], i["contribuicoes"], i["membros"]) for i in dados["em_alta"]] == [("Disco A", 3, 2)]


def test_nao_expoe_dados_privados(ambiente):
    cliente, motor = ambiente
    popular(motor)
    r = cliente.get("/social/comunidade")
    assert r.status_code == 200
    for segredo in ["Segredo", "Nunca publicar", "autor_c", "Disco C", "@example.com", "senha_hash", "usuario_id"]:
        assert segredo not in r.text
    itens = r.json()["atividades"]
    comum = {"tipo", "id", "username", "nome_exibicao", "criada_em", "titulo"}
    adicionais = {"lista": set(), "review": {"id_musicbrainz", "artista", "texto"}, "avaliacao": {"id_musicbrainz", "artista", "nota"}}
    for item in itens:
        assert set(item) == comum | adicionais[item["tipo"]]


def test_privacidade_e_exclusao_refletidas(ambiente):
    cliente, motor = ambiente
    _, publica, _ = popular(motor)
    with Session(motor) as s:
        s.get(ListaMusical, publica).publica = False
        review = s.scalar(select(Review).where(Review.texto == "Review A"))
        s.delete(review); s.commit()
    dados = cliente.get("/social/comunidade").json()
    assert all(i["tipo"] != "lista" for i in dados["atividades"])
    assert all(i.get("texto") != "Review A" for i in dados["atividades"])
    assert dados["em_alta"][0]["contribuicoes"] == 2
    assert all(i["contribuicoes"] == 1 for i in dados["membros_ativos"])


def test_limites_desempate_e_leitura_sem_escritas(ambiente):
    cliente, motor = ambiente
    agora = datetime.now(timezone.utc) - timedelta(days=1)
    with Session(motor) as s:
        for i in range(15):
            usuario = Usuario(username=f"autor_{i}", nome_exibicao=f"Autor {i}", email=f"{i}@example.com", senha_hash="teste")
            obra = Obra(id_musicbrainz=f"00000000-0000-0000-0000-{i:012d}", titulo=f"Disco {i}", tipo="Album")
            s.add_all([usuario, obra]); s.flush()
            s.add(Review(usuario_id=usuario.id, obra_id=obra.id, texto=f"Texto {i}", criada_em=agora))
        s.commit()
    comandos = []

    def registrar(conn, cursor, statement, parameters, context, executemany):
        comandos.append(statement.strip().split()[0].upper())

    event.listen(motor, "before_cursor_execute", registrar)
    try:
        r = cliente.get("/social/comunidade")
    finally:
        event.remove(motor, "before_cursor_execute", registrar)
    assert r.status_code == 200
    dados = r.json()
    assert [i["id"] for i in dados["atividades"]] == list(range(15, 3, -1))
    assert [i["username"] for i in dados["membros_ativos"]] == [f"autor_{i}" for i in range(6)]
    assert [i["titulo"] for i in dados["em_alta"]] == [f"Disco {i}" for i in range(4)]
    assert comandos == ["SELECT"] * 3
    with Session(motor) as s:
        assert s.scalar(select(func.count(Review.id))) == 15
        assert s.scalar(select(func.count(Escuta.id))) == 0


def test_limite_temporal_inclusivo_e_exclusao_do_futuro(ambiente):
    _, motor = ambiente
    agora = datetime(2026, 1, 31, 12, tzinfo=timezone.utc)
    with Session(motor) as s:
        usuario = Usuario(username="autor_a", nome_exibicao="Autor A", email="a@example.com", senha_hash="teste")
        s.add(usuario); s.flush()
        for titulo, data in [("Exata", agora - timedelta(days=30)), ("Antiga", agora - timedelta(days=30, seconds=1)), ("Futura", agora + timedelta(seconds=1))]:
            s.add(ListaMusical(usuario_id=usuario.id, titulo=titulo, publica=True, criada_em=data))
        s.commit()
        dados = consultar_comunidade(s, agora=agora)
        assert [i.titulo for i in dados.atividades] == ["Exata", "Antiga"]
        assert dados.membros_ativos[0].contribuicoes == 1
        assert dados.em_alta == []