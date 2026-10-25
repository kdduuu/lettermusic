from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from backend.app.catalogo import registrar_obra
from backend.app.models import Base, Obra


def preparar_banco():
    motor = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(motor)
    return motor


def test_registrar_obra_sem_duplicar():
    motor = preparar_banco()

    try:
        with Session(motor) as sessao:
            with sessao.begin():
                primeira = registrar_obra(
                    sessao, "obra-teste", "OK Computer", "Album",
                    artista="Radiohead"
                )
                segunda = registrar_obra(
                    sessao, "obra-teste", "OK Computer", "Album",
                    artista="Radiohead"
                )
                assert primeira.id == segunda.id

        with Session(motor) as sessao:
            obras = sessao.scalars(select(Obra)).all()
            assert len(obras) == 1
            assert obras[0].titulo == "OK Computer"
            assert obras[0].artista == "Radiohead"
    finally:
        motor.dispose()


def test_rollback_desfaz_registro_nao_confirmado():
    motor = preparar_banco()

    try:
        with Session(motor) as sessao:
            registrar_obra(sessao, "rollback-id", "Disco temporario")
            sessao.rollback()

        with Session(motor) as sessao:
            obras = sessao.scalars(select(Obra)).all()
            assert obras == []
    finally:
        motor.dispose()


def test_complementa_artista_em_obra_existente():
    motor = preparar_banco()

    try:
        with Session(motor) as sessao:
            registrar_obra(sessao, "obra-teste", "OK Computer", "Album")
            sessao.commit()

            registrar_obra(
                sessao, "obra-teste", "OK Computer", "Album",
                artista="Radiohead"
            )
            sessao.commit()

        with Session(motor) as sessao:
            obra = sessao.scalar(select(Obra))
            assert obra.artista == "Radiohead"
    finally:
        motor.dispose()
