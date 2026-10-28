
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.catalogo import registrar_obra
from backend.app.models import Escuta, ObraOuvida
from backend.app.schemas_interacoes import (
    MarcarOuvidaEntrada,
    ObraInteracao,
    RegistrarEscutaEntrada,
)


def obter_ou_criar_obra(
    sessao: Session,
    dados: ObraInteracao,
):
    """Localiza ou cadastra a obra no catalogo."""

    return registrar_obra(
        sessao=sessao,
        id_musicbrainz=dados.id_musicbrainz,
        titulo=dados.titulo,
        tipo=dados.tipo,
        data_lancamento=dados.data_lancamento,
        artista=dados.artista,
    )


def garantir_obra_ouvida(
    sessao: Session,
    usuario_id: int,
    obra_id: int,
) -> ObraOuvida:
    """Cria a marcacao apenas se ela ainda nao existir."""

    marcacao = sessao.scalar(
        select(ObraOuvida).where(
            ObraOuvida.usuario_id == usuario_id,
            ObraOuvida.obra_id == obra_id,
        )
    )

    if marcacao is not None:
        return marcacao

    marcacao = ObraOuvida(
        usuario_id=usuario_id,
        obra_id=obra_id,
    )

    sessao.add(marcacao)
    sessao.flush()

    return marcacao


def marcar_obra_ouvida(
    sessao: Session,
    usuario_id: int,
    dados: MarcarOuvidaEntrada,
) -> ObraOuvida:
    """Marca uma obra como ouvida, sem registrar escuta."""

    try:
        obra = obter_ou_criar_obra(sessao, dados.obra)

        marcacao = garantir_obra_ouvida(
            sessao,
            usuario_id,
            obra.id,
        )

        sessao.commit()
        sessao.refresh(marcacao)

        return marcacao

    except Exception:
        sessao.rollback()
        raise


def registrar_escuta(
    sessao: Session,
    usuario_id: int,
    dados: RegistrarEscutaEntrada,
) -> Escuta:
    """Registra uma nova escuta e garante o status Ja ouvi."""

    try:
        obra = obter_ou_criar_obra(sessao, dados.obra)

        escuta = Escuta(
            usuario_id=usuario_id,
            obra_id=obra.id,
            ouvida_em=dados.ouvida_em or datetime.now(timezone.utc),
        )

        sessao.add(escuta)

        garantir_obra_ouvida(
            sessao,
            usuario_id,
            obra.id,
        )

        sessao.commit()
        sessao.refresh(escuta)

        return escuta

    except Exception:
        sessao.rollback()
        raise


def listar_obras_ouvidas(
    sessao: Session,
    usuario_id: int,
) -> list[ObraOuvida]:
    """Consulta as ultimas 50 obras marcadas como ouvidas."""

    consulta = (
        select(ObraOuvida)
        .where(ObraOuvida.usuario_id == usuario_id)
        .order_by(
            ObraOuvida.marcada_em.desc(),
            ObraOuvida.id.desc(),
        )
        .limit(50)
    )

    return list(sessao.scalars(consulta))


def listar_escutas(
    sessao: Session,
    usuario_id: int,
) -> list[Escuta]:
    """Consulta as ultimas 50 escutas do usuario."""

    consulta = (
        select(Escuta)
        .where(Escuta.usuario_id == usuario_id)
        .order_by(
            Escuta.ouvida_em.desc(),
            Escuta.id.desc(),
        )
        .limit(50)
    )

    return list(sessao.scalars(consulta))
