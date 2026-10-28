
from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from backend.app.interacoes import (
    garantir_obra_ouvida,
    obter_ou_criar_obra,
)
from backend.app.models import Avaliacao, Escuta, Obra
from backend.app.schemas_interacoes import (
    AvaliacaoCriarEntrada,
    AvaliacaoEditarEntrada,
    AvaliacaoMediaPublica,
    AvaliacaoPublica,
)


class AvaliacaoJaExiste(Exception):
    pass


class AvaliacaoNaoEncontrada(Exception):
    pass


class ObraNaoEncontrada(Exception):
    pass


def formatar_avaliacao(avaliacao: Avaliacao) -> AvaliacaoPublica:
    """Converte a nota interna para estrelas."""

    return AvaliacaoPublica(
        id=avaliacao.id,
        obra_id=avaliacao.obra_id,
        nota=avaliacao.nota_passos / 2,
        criada_em=avaliacao.criada_em,
        atualizada_em=avaliacao.atualizada_em,
    )


def criar_avaliacao(
    sessao: Session,
    usuario_id: int,
    dados: AvaliacaoCriarEntrada,
) -> AvaliacaoPublica:
    """Cria uma avaliacao e registra a primeira escuta."""

    try:
        obra = obter_ou_criar_obra(sessao, dados.obra)

        existente = sessao.scalar(
            select(Avaliacao.id).where(
                Avaliacao.usuario_id == usuario_id,
                Avaliacao.obra_id == obra.id,
            )
        )

        if existente is not None:
            raise AvaliacaoJaExiste()

        avaliacao = Avaliacao(
            usuario_id=usuario_id,
            obra_id=obra.id,
            nota_passos=int(dados.nota * 2),
        )

        sessao.add(avaliacao)

        garantir_obra_ouvida(
            sessao,
            usuario_id,
            obra.id,
        )

        escuta = Escuta(
            usuario_id=usuario_id,
            obra_id=obra.id,
            ouvida_em=datetime.now(timezone.utc),
        )

        sessao.add(escuta)

        sessao.commit()
        sessao.refresh(avaliacao)

        return formatar_avaliacao(avaliacao)

    except Exception:
        sessao.rollback()
        raise


def editar_avaliacao(
    sessao: Session,
    usuario_id: int,
    obra_id: int,
    dados: AvaliacaoEditarEntrada,
) -> AvaliacaoPublica:
    """Atualiza a nota sem criar outra escuta."""

    try:
        avaliacao = sessao.scalar(
            select(Avaliacao).where(
                Avaliacao.usuario_id == usuario_id,
                Avaliacao.obra_id == obra_id,
            )
        )

        if avaliacao is None:
            raise AvaliacaoNaoEncontrada()

        avaliacao.nota_passos = int(dados.nota * 2)
        avaliacao.atualizada_em = datetime.now(timezone.utc)

        sessao.commit()
        sessao.refresh(avaliacao)

        return formatar_avaliacao(avaliacao)

    except Exception:
        sessao.rollback()
        raise


def listar_avaliacoes(
    sessao: Session,
    usuario_id: int,
) -> list[AvaliacaoPublica]:
    """Consulta as ultimas 50 avaliacoes do usuario."""

    consulta = (
        select(Avaliacao)
        .where(Avaliacao.usuario_id == usuario_id)
        .order_by(Avaliacao.id.desc())
        .limit(50)
    )

    avaliacoes = sessao.scalars(consulta).all()

    return [
        formatar_avaliacao(avaliacao)
        for avaliacao in avaliacoes
    ]


def calcular_media_avaliacoes(
    sessao: Session,
    obra_id: int,
) -> AvaliacaoMediaPublica:
    """Calcula a media da comunidade para uma obra."""

    obra = sessao.get(Obra, obra_id)

    if obra is None:
        raise ObraNaoEncontrada()

    consulta = select(
        func.avg(Avaliacao.nota_passos),
        func.count(Avaliacao.id),
    ).where(Avaliacao.obra_id == obra_id)

    media_passos, quantidade = sessao.execute(consulta).one()

    media = (
        round(float(media_passos) / 2, 2)
        if media_passos is not None
        else None
    )

    return AvaliacaoMediaPublica(
        obra_id=obra_id,
        media=media,
        quantidade=quantidade,
    )
