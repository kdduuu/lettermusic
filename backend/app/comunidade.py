"""Leitura da comunidade, sem registrar escutas nem consultar APIs externas."""
from datetime import datetime, timedelta, timezone

from sqlalchemy import Integer, and_, cast, distinct, func, literal, null, select, union_all
from sqlalchemy.orm import Session

from backend.app.models import Avaliacao, ListaMusical, Obra, Review, Usuario
from backend.app.schemas_comunidade import (
    AtividadeAvaliacao, AtividadeLista, AtividadeReview, ComunidadePublica,
    MembroAtivo, ObraEmAlta,
)

JANELA_DIAS = 30
LIMITE_ATIVIDADES = 12
LIMITE_MEMBROS = 6
LIMITE_OBRAS = 4


def consultar_comunidade(sessao: Session, agora: datetime | None = None) -> ComunidadePublica:
    agora = agora if agora is not None else datetime.now(timezone.utc)
    inicio = agora - timedelta(days=JANELA_DIAS)

    # Cada contribuicao e uma linha. A lista so participa enquanto for publica.
    # A data de criacao permanece estavel quando o autor edita uma contribuicao.
    eventos = union_all(
        select(literal("review").label("tipo"), Review.id.label("id"),
               Review.usuario_id.label("usuario_id"), Review.obra_id.label("obra_id"),
               Review.criada_em.label("criada_em"), cast(null(), Integer).label("nota_passos"))
        .where(Review.criada_em <= agora),
        select(literal("avaliacao"), Avaliacao.id, Avaliacao.usuario_id, Avaliacao.obra_id,
               Avaliacao.criada_em, Avaliacao.nota_passos)
        .where(Avaliacao.criada_em <= agora),
        select(literal("lista"), ListaMusical.id, ListaMusical.usuario_id, cast(null(), Integer),
               ListaMusical.criada_em, cast(null(), Integer))
        .where(ListaMusical.publica.is_(True), ListaMusical.criada_em <= agora),
    ).subquery("eventos_publicos")
    e = eventos.c

    recentes = sessao.execute(
        select(e.tipo, e.id, e.criada_em, e.nota_passos, Usuario.username, Usuario.nome_exibicao,
               Obra.id_musicbrainz, Obra.titulo.label("titulo_obra"), Obra.artista,
               Review.texto, ListaMusical.titulo.label("titulo_lista"))
        .select_from(eventos)
        .join(Usuario, Usuario.id == e.usuario_id)
        .outerjoin(Obra, Obra.id == e.obra_id)
        .outerjoin(Review, and_(e.tipo == "review", Review.id == e.id))
        .outerjoin(ListaMusical, and_(e.tipo == "lista", ListaMusical.id == e.id))
        .order_by(e.criada_em.desc(), e.tipo.asc(), e.id.desc())
        .limit(LIMITE_ATIVIDADES)
    ).all()

    atividades = []
    for item in recentes:
        base = dict(id=item.id, username=item.username, nome_exibicao=item.nome_exibicao,
                    criada_em=item.criada_em)
        if item.tipo == "lista":
            atividades.append(AtividadeLista(**base, titulo=item.titulo_lista))
        else:
            obra = dict(id_musicbrainz=item.id_musicbrainz, titulo=item.titulo_obra, artista=item.artista)
            if item.tipo == "review":
                atividades.append(AtividadeReview(**base, **obra, texto=item.texto))
            else:
                atividades.append(AtividadeAvaliacao(**base, **obra, nota=item.nota_passos / 2))

    total = func.count()
    membros = sessao.execute(
        select(Usuario.username, Usuario.nome_exibicao, total.label("contribuicoes"))
        .select_from(eventos)
        .join(Usuario, Usuario.id == e.usuario_id)
        .where(e.criada_em >= inicio)
        .group_by(Usuario.id, Usuario.username, Usuario.nome_exibicao)
        .order_by(total.desc(), Usuario.id.asc())
        .limit(LIMITE_MEMBROS)
    ).all()

    autores = func.count(distinct(e.usuario_id))
    obras = sessao.execute(
        select(Obra.id_musicbrainz, Obra.titulo, Obra.artista,
               total.label("contribuicoes"), autores.label("membros"))
        .select_from(eventos)
        .join(Obra, Obra.id == e.obra_id)
        .where(e.criada_em >= inicio)
        .group_by(Obra.id, Obra.id_musicbrainz, Obra.titulo, Obra.artista)
        .order_by(total.desc(), autores.desc(), Obra.id.asc())
        .limit(LIMITE_OBRAS)
    ).all()

    return ComunidadePublica(
        janela_dias=JANELA_DIAS,
        atividades=atividades,
        membros_ativos=[MembroAtivo(**linha._mapping) for linha in membros],
        em_alta=[ObraEmAlta(**linha._mapping) for linha in obras],
    )