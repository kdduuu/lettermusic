"""Limites persistentes para criacao de contas."""
from backend.app.limites_http import aplicar_limites

JANELA = 900
LIMITE_ORIGEM = 12
LIMITE_EMAIL = 3


def verificar_cadastro(motor, ip, email):
    aplicar_limites(
        motor,
        [
            ("cadastro:origem", ip, LIMITE_ORIGEM, JANELA),
            ("cadastro:email", email.strip().casefold(), LIMITE_EMAIL, JANELA),
        ],
        "Muitas tentativas de cadastro. Aguarde.",
    )
