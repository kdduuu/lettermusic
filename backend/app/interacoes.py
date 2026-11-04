from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.catalogo import obter_ou_registrar_obra_oficial
from backend.app.models import Escuta, ObraOuvida
from backend.app.persistencia import inserir_se_ausente
from backend.app.schemas_interacoes import (
    MarcarOuvidaEntrada,
    ObraInteracao,
    RegistrarEscutaEntrada,
)


def obter_ou_criar_obra(sessao: Session, dados: ObraInteracao):
    """Localiza ou cadastra uma obra usando metadados oficiais."""
    return obter_ou_registrar_obra_oficial(
        sessao=sessao,
        id_musicbrainz=dados.id_musicbrainz,
    )


def garantir_obra_ouvida(
    sessao: Session,
    usuario_id: int,
    obra_id: int,
) -> ObraOuvida:
    """Garante uma unica marcacao, inclusive sob disputa simultanea."""

    consulta = select(ObraOuvida).where(
        ObraOuvida.usuario_id == usuario_id,
        ObraOuvida.obra_id == obra_id,
    )

    marcacao = sessao.scalar(consulta)
    if marcacao is not None:
        return marcacao

    # A chave unica (usuario_id, obra_id) e protegida diretamente
    # pelo banco. Nao precisamos capturar um erro de duplicidade.
    inserir_se_ausente(
        sessao,
        ObraOuvida,
        valores={"usuario_id": usuario_id, "obra_id": obra_id},
        colunas_unicas=[ObraOuvida.usuario_id, ObraOuvida.obra_id],
    )

    return sessao.scalar(consulta)


def marcar_obra_ouvida(
    sessao: Session,
    usuario_id: int,
    dados: MarcarOuvidaEntrada,
) -> ObraOuvida:
    """Marca uma obra como ouvida, sem registrar escuta."""

    try:
        obra = obter_ou_criar_obra(sessao, dados.obra)
        marcacao = garantir_obra_ouvida(sessao, usuario_id, obra.id)
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

        garantir_obra_ouvida(sessao, usuario_id, obra.id)

        sessao.commit()
        sessao.refresh(escuta)
        return escuta
    except Exception:
        sessao.rollback()
        raise


def listar_obras_ouvidas(sessao: Session, usuario_id: int) -> list[ObraOuvida]:
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


def listar_escutas(sessao: Session, usuario_id: int) -> list[Escuta]:
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
