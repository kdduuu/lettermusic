"""Recuperacao e confirmacao por e-mail."""

from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    HTTPException,
    Request,
)
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app import recuperacao_email as rec
from backend.app.database import obter_sessao
from backend.app.models import Usuario
from backend.app.schemas_recuperacao import (
    RedefinirSenha,
    SolicitarRecuperacao,
    TokenRecebido,
)

router = APIRouter(
    prefix="/auth",
    tags=["Recuperacao e Verificacao"],
)

MENSAGEM_GENERICA = (
    "Se existir uma conta com esse e-mail, "
    "voce recebera as instrucoes."
)


def exigir_email_configurado():
    if not rec.email_configurado():
        raise HTTPException(
            503,
            "O envio de e-mails ainda nao esta configurado.",
        )


@router.post("/senha/solicitar")
def solicitar_recuperacao(
    dados: SolicitarRecuperacao,
    request: Request,
    tarefas: BackgroundTasks,
    sessao: Session = Depends(obter_sessao),
):
    exigir_email_configurado()

    ip = request.client.host if request.client else "desconhecido"
    email = str(dados.email).lower()

    rec.limitar_solicitacao(ip, email)

    usuario = sessao.scalar(
        select(Usuario).where(Usuario.email == email)
    )

    if usuario is not None:
        segredo = rec.emitir_token(sessao, usuario, "senha")
        tarefas.add_task(
            rec.enviar_mensagem,
            usuario.email,
            "senha",
            segredo,
        )

    # Mesma resposta para contas existentes e inexistentes.
    return {"mensagem": MENSAGEM_GENERICA}


@router.post("/senha/redefinir", status_code=204)
def redefinir_senha(
    dados: RedefinirSenha,
    sessao: Session = Depends(obter_sessao),
):
    rec.redefinir_senha(
        sessao, dados.token, dados.senha_nova
    )
    return None


@router.post("/email/solicitar")
def solicitar_confirmacao(
    dados: SolicitarRecuperacao,
    request: Request,
    tarefas: BackgroundTasks,
    sessao: Session = Depends(obter_sessao),
):
    exigir_email_configurado()

    ip = request.client.host if request.client else "desconhecido"
    email = str(dados.email).strip().lower()
    rec.limitar_solicitacao(ip, email)

    usuario = sessao.scalar(
        select(Usuario).where(Usuario.email == email)
    )

    if usuario is not None and not usuario.email_confirmado:
        segredo = rec.emitir_token(
            sessao, usuario, "verificacao"
        )
        tarefas.add_task(
            rec.enviar_mensagem,
            usuario.email,
            "verificacao",
            segredo,
        )

    return {
        "mensagem": (
            "Se o e-mail estiver pendente de confirmacao, "
            "enviaremos um novo link."
        )
    }


@router.post("/email/confirmar", status_code=204)
def confirmar_email(
    dados: TokenRecebido,
    sessao: Session = Depends(obter_sessao),
):
    rec.confirmar_email(sessao, dados.token)
    return None
