"""Complementa consultas com dados musicais, sem criar N+1 queries."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.models import Obra


def enriquecer_com_obras(sessao: Session, registros: list) -> list[dict]:
    """Acrescenta metadados das obras a resultados ja filtrados e paginados.

    Uma unica consulta busca as obras da pagina, independentemente
    de quantos favoritos, reviews ou itens ela contenha.
    """
    if not registros:
        return []

    dados = []
    for registro in registros:
        if hasattr(registro, "model_dump"):
            dados.append(registro.model_dump())
        else:
            dados.append({
                coluna.name: getattr(registro, coluna.name)
                for coluna in registro.__table__.columns
            })

    ids = {item["obra_id"] for item in dados}
    obras = {
        obra.id: obra
        for obra in sessao.scalars(select(Obra).where(Obra.id.in_(ids)))
    }

    for item in dados:
        obra = obras.get(item["obra_id"])
        if obra is not None:
            item.update({
                "id_musicbrainz": obra.id_musicbrainz,
                "titulo": obra.titulo,
                "artista": obra.artista,
                "tipo": obra.tipo,
                "data_lancamento": obra.data_lancamento,
            })

    return dados
