"""Permissoes de acesso do frontend ao backend por origem HTTP."""

import os
from urllib.parse import urlsplit

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware


ORIGENS_DESENVOLVIMENTO = (
    "http://localhost:5173,http://127.0.0.1:5173"
)


def obter_origens_permitidas() -> list[str]:
    """Le origens autorizadas, separadas por virgula, sem aceitar curinga."""

    configuracao = os.getenv("CORS_ORIGINS", ORIGENS_DESENVOLVIMENTO)
    origens = [origem.strip() for origem in configuracao.split(",") if origem.strip()]

    for origem in origens:
        url = urlsplit(origem)
        if (
            url.scheme not in {"http", "https"}
            or not url.netloc
            or url.path
            or url.query
            or url.fragment
            or url.username is not None
            or url.password is not None
        ):
            raise ValueError(
                f"Origem CORS invalida: {origem!r}. "
                "Informe somente esquema, host e porta, sem caminhos ou curinga."
            )

    return list(dict.fromkeys(origens))


def configurar_cors(app: FastAPI) -> None:
    """Libera navegadores somente para as origens configuradas."""

    app.add_middleware(
        CORSMiddleware,
        allow_origins=obter_origens_permitidas(),
        allow_credentials=False,  # JWT enviado no header, sem cookie de sessao.
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
        allow_headers=["Authorization", "Content-Type"],
    )
