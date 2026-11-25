"""Contrato, privacidade e atomicidade dos favoritos publicos."""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select, func
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from backend.app.auth import criar_token
from backend.app.database import obter_sessao
from backend.app.main import app
from backend.app.models import (
    Base, Usuario, Obra, Favorito, FavoritoPerfil, Escuta, ObraOuvida, Avaliacao, Review,
)

URL = "/auth/perfil/favoritos"
A = "00000000-0000-0000-0000-000000000001"
B = "00000000-0000-0000-0000-000000000002"
C = "00000000-0000-0000-0000-000000000003"
D = "b1392450-e666-3926-a536-22c65f834433"
INVALIDO = "00000000-0000-0000-0000-000000000099"


@pytest.fixture
def ambiente(monkeypatch):
    monkeypatch.setenv("JWT_SECRET", "chave-ficticia-exclusiva-testes-perfil-123456")
    motor = create_engine("sqlite+pysqlite://", poolclass=StaticPool,
                          connect_args={"check_same_thread": False})
    Base.metadata.create_all(motor)
    with Session(motor) as sessao:
        usuarios = [Usuario(username=n, nome_exibicao=n, email=f"{n}@example.com",
                            senha_hash="hash-ficticio") for n in ("alice", "bruno")]
        sessao.add_all(usuarios)
        sessao.flush()
        headers = [{"Authorization": f"Bearer {criar_token(u.id)}"} for u in usuarios]
        sessao.commit()

    def sessao_teste():
        with Session(motor) as sessao:
            yield sessao

    app.dependency_overrides[obter_sessao] = sessao_teste
    try:
        with TestClient(app) as cliente:
            yield cliente, motor, headers
    finally:
        app.dependency_overrides.pop(obter_sessao, None)
        motor.dispose()


def ids(cliente, username="alice"):
    return [a["id_musicbrainz"] for a in
            cliente.get(f"/usuarios/{username}/social").json()["albuns_favoritos"]]


def test_salvar_reordenar_limpar_e_isolar(ambiente):
    cliente, motor, (alice, bruno) = ambiente
    assert ids(cliente) == []
    assert cliente.put(URL, json={"albuns": [A]}).status_code == 401
    resposta = cliente.put(URL, json={"albuns": [D, B, A, C]}, headers=alice)
    assert resposta.status_code == 200
    assert ids(cliente) == [D, B, A, C]
    assert ids(cliente, "bruno") == []
    assert cliente.put(URL, json={"albuns": [B]}, headers=bruno).status_code == 200
    assert cliente.put(URL, json={"albuns": [C, A]}, headers=alice).status_code == 200
    assert ids(cliente) == [C, A]
    assert ids(cliente, "bruno") == [B]
    with Session(motor) as sessao:
        for modelo in (Favorito, Escuta, ObraOuvida, Avaliacao, Review):
            assert sessao.scalar(select(func.count()).select_from(modelo)) == 0
        assert sessao.scalar(select(func.count()).select_from(Obra)) == 4
    assert cliente.put(URL, json={"albuns": []}, headers=alice).status_code == 200
    assert ids(cliente) == []


@pytest.mark.parametrize("albuns", [[A, A], [A, B, C, D, INVALIDO], ["bad"]])
def test_rejeitar_selecao_invalida(ambiente, albuns):
    cliente, _, (alice, _) = ambiente
    assert cliente.put(URL, json={"albuns": albuns}, headers=alice).status_code == 422
    assert ids(cliente) == []


def test_falha_preserva_selecao_e_desfaz_catalogo(ambiente):
    cliente, motor, (alice, _) = ambiente
    assert cliente.put(URL, json={"albuns": [D]}, headers=alice).status_code == 200
    assert cliente.put(URL, json={"albuns": [A, INVALIDO]}, headers=alice).status_code == 404
    assert ids(cliente) == [D]
    with Session(motor) as sessao:
        assert sessao.scalar(select(func.count()).select_from(Obra)) == 1
        assert sessao.scalar(select(func.count()).select_from(FavoritoPerfil)) == 1


def test_nao_aceita_outro_dono_nem_publica_favorito_privado(ambiente):
    cliente, motor, (alice, _) = ambiente
    with Session(motor) as sessao:
        usuario = sessao.scalar(select(Usuario).where(Usuario.username == "alice"))
        obra = Obra(id_musicbrainz=A, titulo="Privado", tipo="Album")
        sessao.add(obra)
        sessao.flush()
        sessao.add(Favorito(usuario_id=usuario.id, obra_id=obra.id))
        sessao.commit()
    assert ids(cliente) == []
    assert cliente.put(URL, json={"albuns": [A], "usuario_id": 2}, headers=alice).status_code == 422
    assert ids(cliente) == []
    assert ids(cliente, "bruno") == []


def test_nao_aceita_single(ambiente):
    cliente, motor, (alice, _) = ambiente
    with Session(motor) as sessao:
        sessao.add(Obra(id_musicbrainz=A, titulo="Single", tipo="Single"))
        sessao.commit()
    assert cliente.put(URL, json={"albuns": [A]}, headers=alice).status_code == 422
    assert ids(cliente) == []
