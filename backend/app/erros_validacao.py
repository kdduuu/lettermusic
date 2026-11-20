"""Nao devolver valores enviados nos erros de validacao."""
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse


def configurar_erros_validacao(app: FastAPI):
    @app.exception_handler(RequestValidationError)
    async def validar_sem_expor_entrada(
        request: Request, erro: RequestValidationError
    ):
        detalhes = []

        for item in erro.errors():
            detalhes.append({
                campo: item[campo]
                for campo in ("loc", "type", "msg")
                if campo in item
            })

        return JSONResponse(
            status_code=422,
            content={"detail": detalhes},
        )
