
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from backend.app.models import Avaliacao, Escuta, Obra


def dados_basicos_obra(obra: Obra) -> dict:
    """Organiza os metadados de uma obra."""

    return {
        "obra_id": obra.id,
        "id_musicbrainz": obra.id_musicbrainz,
        "titulo": obra.titulo,
        "artista": obra.artista,
        "tipo": obra.tipo,
        "data_lancamento": obra.data_lancamento,
    }


# -----------------------------------------
# OBRAS MAIS OUVIDAS
# -----------------------------------------


def listar_mais_ouvidas(
    sessao: Session,
    limite: int = 10,
) -> list[dict]:
    """Ordena obras pela quantidade total de escutas."""

    total_escutas = func.count(Escuta.id)

    consulta = (
        select(
            Obra,
            total_escutas.label("total_escutas"),
        )
        .join(
            Escuta,
            Escuta.obra_id == Obra.id,
        )
        .group_by(Obra.id)
        .order_by(
            total_escutas.desc(),
            Obra.id.asc(),
        )
        .limit(limite)
    )

    resultados = sessao.execute(consulta).all()

    return [
        {
            **dados_basicos_obra(obra),
            "total_escutas": int(quantidade),
        }
        for obra, quantidade in resultados
    ]


# -----------------------------------------
# OBRAS MAIS BEM AVALIADAS
# -----------------------------------------


def listar_melhor_avaliadas(
    sessao: Session,
    limite: int = 10,
) -> list[dict]:
    """Ordena obras pela media das avaliacoes."""

    media_passos = func.avg(Avaliacao.nota_passos)
    total_avaliacoes = func.count(Avaliacao.id)

    consulta = (
        select(
            Obra,
            media_passos.label("media_passos"),
            total_avaliacoes.label("total_avaliacoes"),
        )
        .join(
            Avaliacao,
            Avaliacao.obra_id == Obra.id,
        )
        .group_by(Obra.id)
        .order_by(
            media_passos.desc(),
            total_avaliacoes.desc(),
            Obra.id.asc(),
        )
        .limit(limite)
    )

    resultados = sessao.execute(consulta).all()

    return [
        {
            **dados_basicos_obra(obra),
            "media": round(float(media) / 2, 2),
            "quantidade_avaliacoes": int(quantidade),
        }
        for obra, media, quantidade in resultados
    ]
