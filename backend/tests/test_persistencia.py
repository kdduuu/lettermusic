
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from backend.app.catalogo import registrar_obra
from backend.app.models import Base, Obra


def test_registrar_obra_sem_duplicar():
    motor = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(motor)

    try:
        with Session(motor) as sessao:
            primeira = registrar_obra(
                sessao, "obra-teste", "OK Computer", "Album"
            )

            segunda = registrar_obra(
                sessao, "obra-teste", "OK Computer", "Album"
            )

            obras = sessao.scalars(select(Obra)).all()

            assert primeira.id == segunda.id
            assert len(obras) == 1
            assert obras[0].titulo == "OK Computer"
    finally:
        motor.dispose()
