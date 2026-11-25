"""Consulta segura do perfil social e dos registros publicos recentes."""

from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from backend.app.models import Avaliacao, ListaMusical, Obra, Review, Usuario
from backend.app.favoritos_perfil import consultar_favoritos_perfil


def instante_utc(data: datetime) -> datetime:
    """Normaliza datas vindas de SQLite/PostgreSQL para ordenacao coerente."""
    if data.tzinfo is None:
        return data.replace(tzinfo=timezone.utc)
    return data.astimezone(timezone.utc)


def consultar_perfil_social(sessao: Session, username: str) -> dict | None:
    """Devolve apenas informacoes publicas, sem registrar visualizacoes."""
    usuario = sessao.scalar(
        select(Usuario).where(Usuario.username == username.lower())
    )
    if usuario is None:
        return None

    total_avaliacoes = sessao.scalar(
        select(func.count(Avaliacao.id)).where(Avaliacao.usuario_id == usuario.id)
    )
    total_reviews = sessao.scalar(
        select(func.count(Review.id)).where(Review.usuario_id == usuario.id)
    )
    total_listas_publicas = sessao.scalar(
        select(func.count(ListaMusical.id)).where(
            ListaMusical.usuario_id == usuario.id,
            ListaMusical.publica.is_(True),
        )
    )

    # Reviews ja sao publicas; consultamos a obra numa unica consulta JOIN.
    reviews = sessao.execute(
        select(Review, Obra)
        .join(Obra, Review.obra_id == Obra.id)
        .where(Review.usuario_id == usuario.id)
        .order_by(Review.criada_em.desc(), Review.id.desc())
        .limit(5)
    ).all()

    reviews_recentes = [
        {
            "id": review.id,
            "obra_id": obra.id,
            "id_musicbrainz": obra.id_musicbrainz,
            "titulo": obra.titulo,
            "artista": obra.artista,
            "texto": review.texto,
            "criada_em": review.criada_em,
            "atualizada_em": review.atualizada_em,
        }
        for review, obra in reviews
    ]

    listas = sessao.scalars(
        select(ListaMusical)
        .where(
            ListaMusical.usuario_id == usuario.id,
            ListaMusical.publica.is_(True),
        )
        .order_by(ListaMusical.criada_em.desc(), ListaMusical.id.desc())
        .limit(5)
    ).all()

    listas_publicas = [
        {
            "id": lista.id,
            "titulo": lista.titulo,
            "descricao": lista.descricao,
            "criada_em": lista.criada_em,
        }
        for lista in listas
    ]

    # Destaques exibem somente reviews e avaliacoes — nao revelam escutas,
    # marcacoes Ja ouvi, favoritos, Quero ouvir ou listas privadas.
    # Cada consulta traz no maximo 5 candidatos; o mesmo album aparece uma vez.
    avaliacoes = sessao.execute(
        select(Avaliacao, Obra)
        .join(Obra, Avaliacao.obra_id == Obra.id)
        .where(Avaliacao.usuario_id == usuario.id)
        .order_by(
            func.coalesce(Avaliacao.atualizada_em, Avaliacao.criada_em).desc(),
            Avaliacao.id.desc(),
        )
        .limit(5)
    ).all()

    candidatos = []
    for review, obra in reviews:
        candidatos.append((instante_utc(review.atualizada_em or review.criada_em), obra))
    for avaliacao, obra in avaliacoes:
        candidatos.append((instante_utc(avaliacao.atualizada_em or avaliacao.criada_em), obra))

    candidatos.sort(key=lambda item: (item[0], item[1].id), reverse=True)
    albuns_recentes = []
    ids_adicionados = set()
    for instante, obra in candidatos:
        if obra.id in ids_adicionados:
            continue
        ids_adicionados.add(obra.id)
        albuns_recentes.append({
            "id_musicbrainz": obra.id_musicbrainz,
            "titulo": obra.titulo,
            "artista": obra.artista,
            "registrado_em": instante,
        })
        if len(albuns_recentes) == 5:
            break

    return {
        "id": usuario.id,
        "username": usuario.username,
        "nome_exibicao": usuario.nome_exibicao,
        "bio": usuario.bio,
        "criado_em": usuario.criado_em,
        "estatisticas": {
            "avaliacoes": int(total_avaliacoes or 0),
            "reviews": int(total_reviews or 0),
            "listas_publicas": int(total_listas_publicas or 0),
        },
        "albuns_favoritos": consultar_favoritos_perfil(sessao, usuario.id),
        "albuns_recentes": albuns_recentes,
        "reviews_recentes": reviews_recentes,
        "listas_publicas": listas_publicas,
    }