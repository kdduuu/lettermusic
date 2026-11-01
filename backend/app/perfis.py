
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from backend.app.models import (
    Avaliacao,
    ListaMusical,
    Obra,
    Review,
    Usuario,
)


def consultar_perfil_social(
    sessao: Session,
    username: str,
) -> dict | None:
    """Consulta dados e atividades publicas de um usuario."""

    usuario = sessao.scalar(
        select(Usuario).where(
            Usuario.username == username.lower()
        )
    )

    if usuario is None:
        return None

    # -----------------------------------------
    # ESTATISTICAS PUBLICAS
    # -----------------------------------------

    total_avaliacoes = sessao.scalar(
        select(func.count(Avaliacao.id)).where(
            Avaliacao.usuario_id == usuario.id
        )
    )

    total_reviews = sessao.scalar(
        select(func.count(Review.id)).where(
            Review.usuario_id == usuario.id
        )
    )

    total_listas_publicas = sessao.scalar(
        select(func.count(ListaMusical.id)).where(
            ListaMusical.usuario_id == usuario.id,
            ListaMusical.publica.is_(True),
        )
    )

    # -----------------------------------------
    # REVIEWS RECENTES
    # -----------------------------------------

    consulta_reviews = (
        select(Review, Obra)
        .join(
            Obra,
            Review.obra_id == Obra.id,
        )
        .where(Review.usuario_id == usuario.id)
        .order_by(
            Review.criada_em.desc(),
            Review.id.desc(),
        )
        .limit(5)
    )

    reviews = sessao.execute(consulta_reviews).all()

    reviews_recentes = [
        {
            "id": review.id,
            "obra_id": obra.id,
            "titulo": obra.titulo,
            "artista": obra.artista,
            "texto": review.texto,
            "criada_em": review.criada_em,
            "atualizada_em": review.atualizada_em,
        }
        for review, obra in reviews
    ]

    # -----------------------------------------
    # LISTAS PUBLICAS
    # -----------------------------------------

    consulta_listas = (
        select(ListaMusical)
        .where(
            ListaMusical.usuario_id == usuario.id,
            ListaMusical.publica.is_(True),
        )
        .order_by(
            ListaMusical.criada_em.desc(),
            ListaMusical.id.desc(),
        )
        .limit(5)
    )

    listas = sessao.scalars(consulta_listas).all()

    listas_publicas = [
        {
            "id": lista.id,
            "titulo": lista.titulo,
            "descricao": lista.descricao,
            "criada_em": lista.criada_em,
        }
        for lista in listas
    ]

    # -----------------------------------------
    # RESPOSTA DO PERFIL
    # -----------------------------------------

    return {
        "id": usuario.id,
        "username": usuario.username,
        "nome_exibicao": usuario.nome_exibicao,
        "bio": usuario.bio,
        "criado_em": usuario.criado_em,
        "estatisticas": {
            "avaliacoes": int(total_avaliacoes or 0),
            "reviews": int(total_reviews or 0),
            "listas_publicas": int(
                total_listas_publicas or 0
            ),
        },
        "reviews_recentes": reviews_recentes,
        "listas_publicas": listas_publicas,
    }
