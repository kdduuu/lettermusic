"""Testes de regressao da entrega de concorrencia (sem banco real)."""

from types import SimpleNamespace
from unittest.mock import Mock, patch

import pytest
from sqlalchemy import create_engine, func, select
from sqlalchemy.dialects import postgresql
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from backend.app.catalogo import registrar_obra
from backend.app.interacoes import garantir_obra_ouvida
from backend.app.itens_lista import (
    ItemJaExisteNaLista,
    _obter_lista_bloqueada,
    adicionar_item_lista,
)
from backend.app.models import Base, Obra, ObraOuvida
from backend.app.reviews import ReviewJaExiste, criar_review
from backend.app.schemas_interacoes import (
    ObraInteracao,
    ReviewCriarEntrada,
)

MBID = "b1392450-e666-3926-a536-22c65f834433"
OBRA = ObraInteracao(
    id_musicbrainz=MBID,
    titulo="OK Computer",
    artista="Radiohead",
    tipo="Album",
)


def erro_de_integridade():
    return IntegrityError(
        statement="INSERT de teste",
        params={},
        orig=Exception("Conflito simulado"),
    )


def test_obra_duplicada_e_reutilizada_sem_comprometer_transacao(monkeypatch):
    """Um conflito de MBID preserva a transacao e reutiliza a obra."""
    motor = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(motor)
    try:
        with Session(motor) as sessao:
            original = Obra(
                id_musicbrainz=MBID,
                titulo="Titulo oficial preservado",
            )
            sessao.add(original)
            sessao.commit()

            consulta_real = sessao.scalar
            consultas = 0

            def simular_disputa(*args, **kwargs):
                nonlocal consultas
                consultas += 1
                if consultas == 1:
                    return None  # Outra transacao inseriu antes do flush.
                return consulta_real(*args, **kwargs)

            monkeypatch.setattr(sessao, "scalar", simular_disputa)

            encontrada = registrar_obra(
                sessao,
                id_musicbrainz=MBID,
                titulo="Titulo concorrente",
            )
            sessao.commit()

            assert encontrada.id == original.id
            assert encontrada.titulo == "Titulo oficial preservado"
            assert consultas == 2
            assert sessao.scalar(select(func.count(Obra.id))) == 1
    finally:
        motor.dispose()


def test_registrar_obra_nao_faz_commit_automatico():
    """Um erro posterior deve poder desfazer o cadastro da obra."""
    motor = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(motor)
    try:
        with Session(motor) as sessao:
            registrar_obra(sessao, id_musicbrainz=MBID, titulo="OK Computer")
            sessao.rollback()
            assert sessao.scalar(select(func.count(Obra.id))) == 0
    finally:
        motor.dispose()


def test_marcacao_duplicada_e_reutilizada(monkeypatch):
    """Uma marcacao ja gravada deve ser reutilizada sem duplicar."""
    motor = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(motor)
    try:
        with Session(motor) as sessao:
            original = ObraOuvida(usuario_id=7, obra_id=3)
            sessao.add(original)
            sessao.commit()

            consulta_real = sessao.scalar
            consultas = 0

            def simular_disputa(*args, **kwargs):
                nonlocal consultas
                consultas += 1
                if consultas == 1:
                    return None
                return consulta_real(*args, **kwargs)

            monkeypatch.setattr(sessao, "scalar", simular_disputa)

            encontrada = garantir_obra_ouvida(sessao, 7, 3)
            sessao.commit()

            assert encontrada.id == original.id
            assert consultas == 2
            assert sessao.scalar(select(func.count(ObraOuvida.id))) == 1
    finally:
        motor.dispose()


@pytest.mark.parametrize("encontrou_duplicata", [True, False])
def test_review_distingue_duplicidade_de_outra_falha(encontrou_duplicata):
    """Apenas a review existente deve virar ReviewJaExiste (HTTP 409)."""
    sessao = Mock(spec=Session)
    sessao.scalar.side_effect = [None, 99 if encontrou_duplicata else None]
    erro = erro_de_integridade()
    sessao.commit.side_effect = erro
    dados = ReviewCriarEntrada(obra=OBRA, texto="Disco excelente.")

    with (
        patch(
            "backend.app.reviews.obter_ou_criar_obra",
            return_value=SimpleNamespace(id=10),
        ),
        patch("backend.app.reviews.garantir_obra_ouvida"),
    ):
        if encontrou_duplicata:
            with pytest.raises(ReviewJaExiste):
                criar_review(sessao, usuario_id=1, dados=dados)
        else:
            with pytest.raises(IntegrityError) as resultado:
                criar_review(sessao, usuario_id=1, dados=dados)
            assert resultado.value is erro

    sessao.rollback.assert_called_once()
    assert sessao.scalar.call_count == 2
    sessao.refresh.assert_not_called()


def test_escrita_em_lista_bloqueia_a_linha_da_lista():
    """No PostgreSQL a consulta deve utilizar SELECT ... FOR UPDATE."""
    sessao = Mock(spec=Session)
    lista = SimpleNamespace(id=5, usuario_id=2)
    sessao.scalar.return_value = lista

    resultado = _obter_lista_bloqueada(sessao, usuario_id=2, lista_id=5)

    consulta = sessao.scalar.call_args.args[0]
    sql = str(consulta.compile(dialect=postgresql.dialect()))
    assert resultado is lista
    assert "FOR UPDATE" in sql


def test_item_lista_duplicado_apos_erro_de_integridade():
    sessao = Mock(spec=Session)
    lista = SimpleNamespace(id=5, usuario_id=2, atualizada_em=None)
    # Lista bloqueada, item inexistente, posicao vazia, item encontrado.
    sessao.scalar.side_effect = [lista, None, None, 42]
    sessao.commit.side_effect = erro_de_integridade()

    with patch(
        "backend.app.itens_lista.obter_ou_criar_obra",
        return_value=SimpleNamespace(id=10),
    ):
        with pytest.raises(ItemJaExisteNaLista):
            adicionar_item_lista(sessao, 2, 5, OBRA)

    sessao.rollback.assert_called_once()
    assert sessao.scalar.call_count == 4
