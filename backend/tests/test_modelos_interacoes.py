
from datetime import datetime, timezone

import pytest
from sqlalchemy import create_engine, event, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from backend.app.models import (
    Avaliacao,
    Base,
    Escuta,
    Obra,
    ObraOuvida,
    Review,
    Usuario,
)


@pytest.fixture
def banco():
    """Cria um banco temporario para cada teste."""
    motor = create_engine("sqlite+pysqlite:///:memory:")

    def ativar_chaves_estrangeiras(conexao, registro):
        conexao.execute("PRAGMA foreign_keys=ON")

    event.listen(motor, "connect", ativar_chaves_estrangeiras)
    Base.metadata.create_all(motor)

    with Session(motor) as sessao:
        usuario = Usuario(
            username="radiohead_fan",
            nome_exibicao="Radiohead Fan",
            email="teste@example.com",
            senha_hash="hash-ficticio",
        )
        obra = Obra(
            id_musicbrainz="obra-teste",
            titulo="OK Computer",
            artista="Radiohead",
            tipo="Album",
        )

        sessao.add_all([usuario, obra])
        sessao.flush()

        usuario_id = usuario.id
        obra_id = obra.id
        sessao.commit()

    try:
        yield motor, usuario_id, obra_id
    finally:
        motor.dispose()


def test_marcar_obra_ouvida_sem_criar_escuta(banco):
    motor, usuario_id, obra_id = banco

    with Session(motor) as sessao:
        sessao.add(ObraOuvida(usuario_id=usuario_id, obra_id=obra_id))
        sessao.commit()

        marcacoes = sessao.scalars(select(ObraOuvida)).all()
        escutas = sessao.scalars(select(Escuta)).all()

        assert len(marcacoes) == 1
        assert len(escutas) == 0


def test_nao_permite_marcacao_duplicada(banco):
    motor, usuario_id, obra_id = banco

    with Session(motor) as sessao:
        sessao.add(ObraOuvida(usuario_id=usuario_id, obra_id=obra_id))
        sessao.commit()

        sessao.add(ObraOuvida(usuario_id=usuario_id, obra_id=obra_id))

        with pytest.raises(IntegrityError):
            sessao.commit()

        sessao.rollback()


def test_permite_varias_escutas_da_mesma_obra(banco):
    motor, usuario_id, obra_id = banco

    with Session(motor) as sessao:
        for _ in range(3):
            sessao.add(
                Escuta(
                    usuario_id=usuario_id,
                    obra_id=obra_id,
                    ouvida_em=datetime.now(timezone.utc),
                )
            )

        sessao.commit()

        escutas = sessao.scalars(select(Escuta)).all()
        assert len(escutas) == 3


def test_avaliacao_aceita_notas_e_edicao(banco):
    motor, usuario_id, obra_id = banco

    with Session(motor) as sessao:
        avaliacao = Avaliacao(
            usuario_id=usuario_id,
            obra_id=obra_id,
            nota_passos=1,
        )
        sessao.add(avaliacao)
        sessao.commit()

        assert avaliacao.nota_passos == 1

        avaliacao.nota_passos = 10
        avaliacao.atualizada_em = datetime.now(timezone.utc)
        sessao.commit()

        assert avaliacao.nota_passos == 10


def test_rejeita_notas_invalidas(banco):
    motor, usuario_id, obra_id = banco

    with Session(motor) as sessao:
        for nota in [0, -1, 11]:
            sessao.add(
                Avaliacao(
                    usuario_id=usuario_id,
                    obra_id=obra_id,
                    nota_passos=nota,
                )
            )

            with pytest.raises(IntegrityError):
                sessao.commit()

            sessao.rollback()


def test_nao_permite_avaliacao_duplicada(banco):
    motor, usuario_id, obra_id = banco

    with Session(motor) as sessao:
        sessao.add(
            Avaliacao(
                usuario_id=usuario_id,
                obra_id=obra_id,
                nota_passos=8,
            )
        )
        sessao.commit()

        sessao.add(
            Avaliacao(
                usuario_id=usuario_id,
                obra_id=obra_id,
                nota_passos=9,
            )
        )

        with pytest.raises(IntegrityError):
            sessao.commit()

        sessao.rollback()


def test_review_nao_permite_duplicidade_ou_texto_vazio(banco):
    motor, usuario_id, obra_id = banco

    with Session(motor) as sessao:
        review = Review(
            usuario_id=usuario_id,
            obra_id=obra_id,
            texto="Um album excelente.",
        )
        sessao.add(review)
        sessao.commit()

        sessao.add(
            Review(
                usuario_id=usuario_id,
                obra_id=obra_id,
                texto="Segunda review.",
            )
        )

        with pytest.raises(IntegrityError):
            sessao.commit()

        sessao.rollback()

        review = sessao.scalar(select(Review))
        review.texto = "   "

        with pytest.raises(IntegrityError):
            sessao.commit()

        sessao.rollback()


def test_excluir_usuario_remove_interacoes(banco):
    motor, usuario_id, obra_id = banco

    with Session(motor) as sessao:
        sessao.add_all(
            [
                ObraOuvida(usuario_id=usuario_id, obra_id=obra_id),
                Escuta(usuario_id=usuario_id, obra_id=obra_id),
                Avaliacao(
                    usuario_id=usuario_id,
                    obra_id=obra_id,
                    nota_passos=9,
                ),
                Review(
                    usuario_id=usuario_id,
                    obra_id=obra_id,
                    texto="Minha review.",
                ),
            ]
        )
        sessao.commit()

        usuario = sessao.get(Usuario, usuario_id)
        sessao.delete(usuario)
        sessao.commit()

        for modelo in [ObraOuvida, Escuta, Avaliacao, Review]:
            assert sessao.scalars(select(modelo)).all() == []
