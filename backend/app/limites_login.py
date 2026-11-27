"""Reserva tentativas antes do hash de senha, inclusive concorrentes."""
from backend.app.limites_http import aplicar_limites

JANELA = 60
LIMITE_CONTA = 5
LIMITE_ORIGEM = 40


def verificar(motor, ip, identificador):
    aplicar_limites(
        motor,
        [
            ("login:origem", ip, LIMITE_ORIGEM, JANELA),
            ("login:conta", identificador.strip().casefold(), LIMITE_CONTA, JANELA),
        ],
        "Muitas tentativas. Tente novamente em um minuto.",
    )
