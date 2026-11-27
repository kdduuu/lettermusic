"""Operacoes da conta autenticada."""
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import delete, update
from sqlalchemy.orm import Session

from backend.app.auth import obter_usuario_atual
from backend.app.database import obter_sessao
from backend.app.limites_http import aplicar_limites
from backend.app.models import Usuario, TokenConta
from backend.app.schemas_conta import (
    ContaPrivada,
    AtualizarContaEntrada,
    AlterarSenhaEntrada,
    ExcluirContaEntrada,
)
from backend.app.usuarios import protetor_senhas

router = APIRouter(prefix="/auth", tags=["Conta e Seguranca"])

LIMITE_OPERACOES_SENSIVEIS = 5
JANELA_OPERACOES_SENSIVEIS = 300


def limitar_operacao_sensivel(sessao: Session, usuario: Usuario):
    """Compartilha o limite de confirmacao de senha entre as duas rotas."""
    aplicar_limites(
        sessao.get_bind(),
        [(
            "conta:senha-atual", str(usuario.id),
            LIMITE_OPERACOES_SENSIVEIS, JANELA_OPERACOES_SENSIVEIS,
        )],
        "Muitas tentativas. Aguarde antes de tentar novamente.",
    )


@router.get("/conta", response_model=ContaPrivada)
def consultar_conta(
    usuario: Usuario = Depends(obter_usuario_atual),
):
    # E-mail permanece privado: nao alterar o contrato publico.
    return usuario


@router.patch("/conta", response_model=ContaPrivada)
def editar_conta(
    dados: AtualizarContaEntrada,
    usuario: Usuario = Depends(obter_usuario_atual),
    sessao: Session = Depends(obter_sessao),
):
    usuario.nome_exibicao = dados.nome_exibicao
    sessao.commit()
    sessao.refresh(usuario)
    return usuario


@router.post("/senha", status_code=204)
def alterar_senha(
    dados: AlterarSenhaEntrada,
    usuario: Usuario = Depends(obter_usuario_atual),
    sessao: Session = Depends(obter_sessao),
):
    limitar_operacao_sensivel(sessao, usuario)

    if not protetor_senhas.verify(
        dados.senha_atual, usuario.senha_hash
    ):
        raise HTTPException(400, "Senha atual incorreta.")

    if dados.senha_atual == dados.senha_nova:
        raise HTTPException(
            422, "A nova senha deve ser diferente da atual."
        )

    anterior = usuario.senha_hash
    novo_hash = protetor_senhas.hash(dados.senha_nova)

    resultado = sessao.execute(
        update(Usuario)
        .where(
            Usuario.id == usuario.id,
            Usuario.senha_hash == anterior,
        )
        .values(
            senha_hash=novo_hash,
            sessao_versao=Usuario.sessao_versao + 1,
        )
        .execution_options(synchronize_session=False)
    )

    if resultado.rowcount != 1:
        sessao.rollback()
        raise HTTPException(
            409, "A conta foi modificada. Tente novamente."
        )

    # A troca manual tambem invalida links de recuperacao
    # pendentes, na mesma transacao da nova senha.
    sessao.execute(
        update(TokenConta)
        .where(
            TokenConta.usuario_id == usuario.id,
            TokenConta.finalidade == "senha",
            TokenConta.usado_em.is_(None),
        )
        .values(usado_em=datetime.now(timezone.utc))
    )

    sessao.commit()
    # JWTs e links de recuperacao anteriores sao invalidados.
    return None


@router.delete("/conta", status_code=204)
def excluir_conta(
    dados: ExcluirContaEntrada,
    usuario: Usuario = Depends(obter_usuario_atual),
    sessao: Session = Depends(obter_sessao),
):
    limitar_operacao_sensivel(sessao, usuario)

    if not protetor_senhas.verify(
        dados.senha_atual, usuario.senha_hash
    ):
        raise HTTPException(400, "Senha atual incorreta.")

    resultado = sessao.execute(
        delete(Usuario)
        .where(
            Usuario.id == usuario.id,
            Usuario.senha_hash == usuario.senha_hash,
        )
        .execution_options(synchronize_session=False)
    )

    if resultado.rowcount != 1:
        sessao.rollback()
        raise HTTPException(
            409, "A conta foi modificada. Tente novamente."
        )

    # As referencias pessoais possuem ON DELETE CASCADE.
    # As obras do catalogo compartilhado nao sao removidas.
    sessao.commit()
    return None


@router.post("/sessoes/revogar", status_code=204)
def revogar_sessoes(
    usuario: Usuario = Depends(obter_usuario_atual),
    sessao: Session = Depends(obter_sessao),
):
    sessao.execute(
        update(Usuario)
        .where(Usuario.id == usuario.id)
        .values(sessao_versao=Usuario.sessao_versao + 1)
        .execution_options(synchronize_session=False)
    )
    sessao.commit()
    return None