"""Leitura publica de reviews: autor, obra e nota atual, sem dados privados."""
from sqlalchemy import and_, select
from sqlalchemy.orm import Session

from backend.app.models import Avaliacao, Obra, Review, Usuario
from backend.app.schemas_feed import PaginaReviews, ReviewFeed


def listar_feed_reviews(sessao: Session, pagina: int, por_pagina: int) -> PaginaReviews:
    consulta = (
        select(Review, Usuario.username, Usuario.nome_exibicao, Obra, Avaliacao.nota_passos)
        .join(Usuario, Usuario.id == Review.usuario_id)
        .join(Obra, Obra.id == Review.obra_id)
        .outerjoin(Avaliacao, and_(
            Avaliacao.usuario_id == Review.usuario_id,
            Avaliacao.obra_id == Review.obra_id,
        ))
        .order_by(Review.criada_em.desc(), Review.id.desc())
        .offset((pagina - 1) * por_pagina)
        .limit(por_pagina + 1)
    )
    registros = sessao.execute(consulta).all()
    return PaginaReviews(
        pagina=pagina,
        por_pagina=por_pagina,
        tem_proxima=len(registros) > por_pagina,
        resultados=[
            ReviewFeed(
                id=review.id, username=username, nome_exibicao=nome,
                id_musicbrainz=obra.id_musicbrainz, titulo=obra.titulo,
                artista=obra.artista, texto=review.texto,
                nota=passos / 2 if passos is not None else None,
                criada_em=review.criada_em, atualizada_em=review.atualizada_em,
            )
            for review, username, nome, obra, passos in registros[:por_pagina]
        ],
    )