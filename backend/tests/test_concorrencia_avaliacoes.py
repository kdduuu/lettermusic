
from types import SimpleNamespace
from unittest.mock import Mock, patch

import pytest

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from backend.app.avaliacoes import (
    AvaliacaoJaExiste,
    criar_avaliacao,
)
from backend.app.schemas_interacoes import (
    AvaliacaoCriarEntrada,
    ObraInteracao,
)


OBRA_TESTE = ObraInteracao(
    id_musicbrainz="b1392450-e666-3926-a536-22c65f834433",
    titulo="OK Computer",
    artista="Radiohead",
    tipo="Album",
    data_lancamento="1997-05-21",
)

DADOS_AVALIACAO = AvaliacaoCriarEntrada(
    obra=OBRA_TESTE,
    nota="4.5",
)


def criar_erro_integridade():
    """Simula uma falha de integridade do banco."""

    return IntegrityError(
        statement="INSERT INTO avaliacoes (...) VALUES (...)",
        params={},
        orig=Exception("Conflito simulado"),
    )


# -----------------------------------------
# CONFLITO SIMULTANEO
# -----------------------------------------


def test_avaliacao_criada_por_outra_requisicao():
    """Uma disputa pela mesma avaliacao deve gerar 409 na API."""

    sessao = Mock(spec=Session)

    # Antes da gravacao: nao existe avaliacao.
    # Apos o rollback: outra requisicao ja a cadastrou.
    sessao.scalar.side_effect = [None, 99]

    sessao.commit.side_effect = criar_erro_integridade()

    with (
        patch(
            "backend.app.avaliacoes.obter_ou_criar_obra",
            return_value=SimpleNamespace(id=10),
        ),
        patch(
            "backend.app.avaliacoes.garantir_obra_ouvida"
        ),
    ):
        with pytest.raises(AvaliacaoJaExiste):
            criar_avaliacao(
                sessao=sessao,
                usuario_id=1,
                dados=DADOS_AVALIACAO,
            )

    assert sessao.scalar.call_count == 2
    sessao.commit.assert_called_once()
    sessao.rollback.assert_called_once()
    sessao.refresh.assert_not_called()


# -----------------------------------------
# OUTROS ERROS DE INTEGRIDADE
# -----------------------------------------


def test_nao_confunde_outro_erro_com_avaliacao_duplicada():
    """Preserva falhas que nao representam duplicidade."""

    sessao = Mock(spec=Session)

    # Nenhuma avaliacao existe antes ou depois da falha.
    sessao.scalar.side_effect = [None, None]

    erro_original = criar_erro_integridade()
    sessao.commit.side_effect = erro_original

    with (
        patch(
            "backend.app.avaliacoes.obter_ou_criar_obra",
            return_value=SimpleNamespace(id=10),
        ),
        patch(
            "backend.app.avaliacoes.garantir_obra_ouvida"
        ),
    ):
        with pytest.raises(IntegrityError) as resultado:
            criar_avaliacao(
                sessao=sessao,
                usuario_id=1,
                dados=DADOS_AVALIACAO,
            )

    assert resultado.value is erro_original
    assert sessao.scalar.call_count == 2
    sessao.rollback.assert_called_once()
    sessao.refresh.assert_not_called()


# -----------------------------------------
# AVALIACAO JA EXISTENTE
# -----------------------------------------


def test_avaliacao_existente_nao_tenta_gravar():
    """Impede uma segunda avaliacao antes mesmo do commit."""

    sessao = Mock(spec=Session)

    # A avaliacao ja existe na primeira consulta.
    sessao.scalar.return_value = 99

    with patch(
        "backend.app.avaliacoes.obter_ou_criar_obra",
        return_value=SimpleNamespace(id=10),
    ):
        with pytest.raises(AvaliacaoJaExiste):
            criar_avaliacao(
                sessao=sessao,
                usuario_id=1,
                dados=DADOS_AVALIACAO,
            )

    sessao.commit.assert_not_called()
    sessao.add.assert_not_called()
    sessao.rollback.assert_called_once()
