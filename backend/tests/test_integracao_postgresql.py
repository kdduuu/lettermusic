"""Testes reais de concorrencia em PostgreSQL, isolados de bancos de uso normal.

Ative definindo LETTERMUSIC_TEST_DATABASE_URL com uma URL PostgreSQL cujo
nome de banco termine em _test. Sem a variavel, estes testes sao ignorados.
Nenhuma tabela em public e modificada: cada teste usa seu proprio schema
temporario, criado e removido automaticamente.
"""

import os
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
from uuid import uuid4

import pytest
from sqlalchemy import create_engine, func, select
from sqlalchemy.engine import make_url
from sqlalchemy.orm import Session
from sqlalchemy.schema import CreateSchema, DropSchema

from backend.app.biblioteca import ItemJaExiste, adicionar_favorito
from backend.app.catalogo import registrar_obra
from backend.app.interacoes import garantir_obra_ouvida
from backend.app.models import Base, Favorito, Obra, ObraOuvida, Usuario
from backend.app.schemas_interacoes import ObraInteracao


MBID = "b1392450-e666-3926-a536-22c65f834433"


@pytest.fixture
def banco_postgresql():
    """Cria um schema exclusivo e temporario em um banco marcado _test."""

    endereco = os.getenv("LETTERMUSIC_TEST_DATABASE_URL")
    if not endereco:
        pytest.skip("Configure LETTERMUSIC_TEST_DATABASE_URL para rodar no PostgreSQL")

    url = make_url(endereco)
    if (
        url.get_backend_name() != "postgresql"
        or not url.database
        or not url.database.endswith("_test")
    ):
        pytest.fail(
            "Protecao ativa: use PostgreSQL e um banco com nome terminado em _test."
        )

    motor_principal = create_engine(url, pool_pre_ping=True)
    esquema = f"lt_integracao_{uuid4().hex[:12]}"
    esquema_criado = False

    try:
        with motor_principal.begin() as conexao:
            conexao.execute(CreateSchema(esquema))
            esquema_criado = True

        motor = motor_principal.execution_options(
            schema_translate_map={None: esquema}
        )
        Base.metadata.create_all(motor)
        yield motor
    finally:
        if esquema_criado:
            with motor_principal.begin() as conexao:
                conexao.execute(DropSchema(esquema, cascade=True))
        motor_principal.dispose()


def executar_simultaneamente(operacao):
    """Inicia duas sessoes em paralelo; propaga erros e limita a espera."""
    inicio = Barrier(2)

    def executar():
        inicio.wait(timeout=10)
        return operacao()

    with ThreadPoolExecutor(max_workers=2) as executor:
        resultados = [executor.submit(executar) for _ in range(2)]
        return [resultado.result(timeout=25) for resultado in resultados]


def test_mesmo_mbid_em_duas_transacoes(banco_postgresql):
    """Duas insercoes concorrentes resolvem para uma unica obra."""

    def cadastrar():
        with Session(banco_postgresql) as sessao:
            obra = registrar_obra(
                sessao,
                id_musicbrainz=MBID,
                titulo="OK Computer",
                artista="Radiohead",
                tipo="Album",
            )
            obra_id = obra.id
            sessao.commit()
            return obra_id

    ids = executar_simultaneamente(cadastrar)
    assert ids[0] == ids[1]

    with Session(banco_postgresql) as sessao:
        assert sessao.scalar(select(func.count()).select_from(Obra)) == 1


def preparar_usuario_e_obra(motor):
    """Prepara chaves existentes sem depender de requisicoes externas."""
    with Session(motor) as sessao:
        usuario = Usuario(
            username="teste_concorrencia",
            nome_exibicao="Teste Concorrencia",
            email="concorrencia@example.com",
            senha_hash="hash-ficticio",
        )
        obra = Obra(
            id_musicbrainz=MBID,
            titulo="OK Computer",
            artista="Radiohead",
            tipo="Album",
        )
        sessao.add_all([usuario, obra])
        sessao.flush()
        ids = (usuario.id, obra.id)
        sessao.commit()
        return ids


def test_ja_ouvi_simultaneo_sem_duplicar(banco_postgresql):
    """Marcacoes concorrentes devem apontar para o mesmo registro."""
    usuario_id, obra_id = preparar_usuario_e_obra(banco_postgresql)

    def marcar():
        with Session(banco_postgresql) as sessao:
            marcacao = garantir_obra_ouvida(sessao, usuario_id, obra_id)
            marcacao_id = marcacao.id
            sessao.commit()
            return marcacao_id

    ids = executar_simultaneamente(marcar)
    assert ids[0] == ids[1]

    with Session(banco_postgresql) as sessao:
        assert sessao.scalar(select(func.count()).select_from(ObraOuvida)) == 1


def test_favoritos_concorrentes_um_sucesso_um_conflito(banco_postgresql):
    """Favorito duplicado nao deve virar erro inesperado do banco."""
    usuario_id, _ = preparar_usuario_e_obra(banco_postgresql)
    entrada = ObraInteracao(id_musicbrainz=MBID)

    def favoritar():
        with Session(banco_postgresql) as sessao:
            try:
                adicionar_favorito(sessao, usuario_id, entrada)
                return "criado"
            except ItemJaExiste:
                return "duplicado"

    resultados = executar_simultaneamente(favoritar)
    assert sorted(resultados) == ["criado", "duplicado"]

    with Session(banco_postgresql) as sessao:
        assert sessao.scalar(select(func.count()).select_from(Favorito)) == 1


def test_rollback_da_obra_em_postgresql(banco_postgresql):
    """Um cadastro nao confirmado nao pode persistir no banco."""
    with Session(banco_postgresql) as sessao:
        registrar_obra(sessao, MBID, "OK Computer", artista="Radiohead")
        sessao.rollback()

    with Session(banco_postgresql) as sessao:
        assert sessao.scalar(select(func.count()).select_from(Obra)) == 0


@pytest.mark.parametrize("finalidade", ["senha", "verificacao"])
def test_tokens_distintos_da_mesma_conta_em_concorrencia(banco_postgresql, finalidade):
    """Duas operacoes concorrentes nao podem consumir dois links da mesma conta."""
    from fastapi import HTTPException
    from backend.app import recuperacao_email as rec
    from backend.app.models import TokenConta
    from backend.app.usuarios import protetor_senhas

    usuario_id, _ = preparar_usuario_e_obra(banco_postgresql)
    with Session(banco_postgresql) as sessao:
        usuario = sessao.get(Usuario, usuario_id)
        versao = usuario.sessao_versao
        tokens = [rec.emitir_token(sessao, usuario, finalidade) for _ in range(2)]

    inicio = Barrier(2)

    def executar(indice):
        with Session(banco_postgresql) as sessao:
            inicio.wait(timeout=10)
            try:
                if finalidade == "senha":
                    rec.redefinir_senha(sessao, tokens[indice], f"NovaSenhaSegura#{indice}2026")
                else:
                    rec.confirmar_email(sessao, tokens[indice])
                return indice
            except HTTPException as erro:
                assert erro.status_code == 400
                return None

    with ThreadPoolExecutor(max_workers=2) as executor:
        tarefas = [executor.submit(executar, i) for i in range(2)]
        resultados = [tarefa.result(timeout=25) for tarefa in tarefas]
    assert sum(r is not None for r in resultados) == 1
    vencedor = next(r for r in resultados if r is not None)
    with Session(banco_postgresql) as sessao:
        usuario = sessao.get(Usuario, usuario_id)
        assert sessao.scalar(select(func.count()).select_from(TokenConta).where(
            TokenConta.usuario_id == usuario_id, TokenConta.usado_em.is_(None)
        )) == 0
        if finalidade == "senha":
            assert usuario.sessao_versao == versao + 1
            assert protetor_senhas.verify(f"NovaSenhaSegura#{vencedor}2026", usuario.senha_hash)
        else:
            assert usuario.email_confirmado


def test_troca_manual_e_recuperacao_concorrentes(banco_postgresql):
    """Troca autenticada e recuperacao usam a mesma ordem de bloqueios."""
    from fastapi import HTTPException
    from backend.app import recuperacao_email as rec
    from backend.app.rotas_conta import alterar_senha
    from backend.app.schemas_conta import AlterarSenhaEntrada
    from backend.app.usuarios import protetor_senhas

    usuario_id, _ = preparar_usuario_e_obra(banco_postgresql)
    original = "SenhaOriginal#2026"
    with Session(banco_postgresql) as sessao:
        usuario = sessao.get(Usuario, usuario_id)
        usuario.senha_hash = protetor_senhas.hash(original)
        sessao.commit()
        versao = usuario.sessao_versao
        token = rec.emitir_token(sessao, usuario, "senha")

    inicio = Barrier(2)

    def manual():
        with Session(banco_postgresql) as sessao:
            usuario = sessao.get(Usuario, usuario_id)
            inicio.wait(timeout=10)
            try:
                alterar_senha(AlterarSenhaEntrada(senha_atual=original, senha_nova="SenhaManual#2026"), usuario, sessao)
                return "manual"
            except HTTPException as erro:
                assert erro.status_code in (400, 409)
                return None

    def recuperacao():
        with Session(banco_postgresql) as sessao:
            inicio.wait(timeout=10)
            try:
                rec.redefinir_senha(sessao, token, "SenhaRecuperada#2026")
                return "recuperacao"
            except HTTPException as erro:
                assert erro.status_code == 400
                return None

    with ThreadPoolExecutor(max_workers=2) as executor:
        tarefas = [executor.submit(manual), executor.submit(recuperacao)]
        resultados = [tarefa.result(timeout=25) for tarefa in tarefas]
    assert sum(r is not None for r in resultados) == 1
    with Session(banco_postgresql) as sessao:
        usuario = sessao.get(Usuario, usuario_id)
        assert usuario.sessao_versao == versao + 1
        senha = "SenhaManual#2026" if "manual" in resultados else "SenhaRecuperada#2026"
        assert protetor_senhas.verify(senha, usuario.senha_hash)
