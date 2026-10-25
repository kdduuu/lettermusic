from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.catalogo import registrar_obra
from backend.app.database import criar_motor
from backend.app.models import Obra


ID_OBRA = "b1392450-e666-3926-a536-22c65f834433"


def main():
    motor = criar_motor()

    try:
        with Session(motor) as sessao:
            with sessao.begin():
                obra = registrar_obra(
                    sessao,
                    ID_OBRA,
                    "OK Computer",
                    "Album",
                    "1997-05-21",
                    artista="Radiohead"
                )
                identificador = obra.id

            # A transacao foi confirmada ao sair de sessao.begin().
            encontrada = sessao.scalar(
                select(Obra).where(Obra.id_musicbrainz == ID_OBRA)
            )
            print(f"Obra salva: ID {identificador}")
            print(f"Obra consultada: {encontrada.titulo}")
            print(f"Artista: {encontrada.artista}")
    finally:
        motor.dispose()


if __name__ == "__main__":
    main()
