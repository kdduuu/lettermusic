from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from backend.app.interacoes import (
    garantir_obra_ouvida,
    obter_ou_criar_obra,
)
from backend.app.models import Escuta, Obra, Review
from backend.app.schemas_interacoes import (
    ReviewCriarEntrada,
    ReviewEditarEntrada,
)


class ReviewJaExiste(Exception):
    pass


class ReviewNaoEncontrada(Exception):
    pass


class ObraDeReviewNaoEncontrada(Exception):
    pass


def criar_review(
    sessao: Session,
    usuario_id: int,
    dados: ReviewCriarEntrada,
) -> Review:
    """Publica uma review e registra uma escuta."""

    obra_id = None

    try:
        obra = obter_ou_criar_obra(sessao, dados.obra)
        obra_id = obra.id

        existente = sessao.scalar(
            select(Review.id).where(
                Review.usuario_id == usuario_id,
                Review.obra_id == obra_id,
            )
        )
        if existente is not None:
            raise ReviewJaExiste()

        review = Review(
            usuario_id=usuario_id,
            obra_id=obra_id,
            texto=dados.texto,
        )
        sessao.add(review)

        garantir_obra_ouvida(sessao, usuario_id, obra_id)
        sessao.add(
            Escuta(
                usuario_id=usuario_id,
                obra_id=obra_id,
                ouvida_em=datetime.now(timezone.utc),
            )
        )

        sessao.commit()
        sessao.refresh(review)
        return review

    except IntegrityError as erro:
        sessao.rollback()

        if obra_id is not None:
            duplicada = sessao.scalar(
                select(Review.id).where(
                    Review.usuario_id == usuario_id,
                    Review.obra_id == obra_id,
                )
            )
            if duplicada is not None:
                raise ReviewJaExiste() from erro
        raise

    except Exception:
        sessao.rollback()
        raise


def editar_review(
    sessao: Session,
    usuario_id: int,
    obra_id: int,
    dados: ReviewEditarEntrada,
) -> Review:
    """Edita apenas a review do usuario autenticado."""

    try:
        review = sessao.scalar(
            select(Review).where(
                Review.usuario_id == usuario_id,
                Review.obra_id == obra_id,
            )
        )
        if review is None:
            raise ReviewNaoEncontrada()

        review.texto = dados.texto
        review.atualizada_em = datetime.now(timezone.utc)
        sessao.commit()
        sessao.refresh(review)
        return review
    except Exception:
        sessao.rollback()
        raise


def excluir_review(
    sessao: Session,
    usuario_id: int,
    obra_id: int,
) -> None:
    """Exclui a review, preservando o historico de escutas."""

    try:
        review = sessao.scalar(
            select(Review).where(
                Review.usuario_id == usuario_id,
                Review.obra_id == obra_id,
            )
        )
        if review is None:
            raise ReviewNaoEncontrada()

        sessao.delete(review)
        sessao.commit()
    except Exception:
        sessao.rollback()
        raise


def listar_minhas_reviews(sessao: Session, usuario_id: int) -> list[Review]:
    consulta = (
        select(Review)
        .where(Review.usuario_id == usuario_id)
        .order_by(Review.criada_em.desc(), Review.id.desc())
        .limit(50)
    )
    return list(sessao.scalars(consulta))


def listar_reviews_da_obra(sessao: Session, obra_id: int) -> list[Review]:
    obra = sessao.get(Obra, obra_id)
    if obra is None:
        raise ObraDeReviewNaoEncontrada()

    consulta = (
        select(Review)
        .where(Review.obra_id == obra_id)
        .order_by(Review.criada_em.desc(), Review.id.desc())
        .limit(50)
    )
    return list(sessao.scalars(consulta))
