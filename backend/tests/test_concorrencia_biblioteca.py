
from types import SimpleNamespace
from unittest.mock import Mock, patch

import pytest

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from backend.app.biblioteca import (
    ItemJaExiste,
    _adicionar,
)
from backend.app.models import Favorito, QueroOuvir
from backend.app.schemas_interacoes import ObraInteracao


OBRA_TESTE = ObraInteracao(
    id_musicbrainz="b1392450-e666-3926-a536-22c65f834433",
    titulo="OK Computer",
    artista="Radiohead",
    tipo="Album",
    data_lancamento="1997-05-21",
)


def criar_erro_integridade():
    """Simula uma violacao de restricao do banco."""

    return IntegrityError(
        statement="INSERT INTO biblioteca (...) VALUES (...)",
        params={},
        orig=Exception("Conflito simulado"),
    )


# -----------------------------------------
# DUPLICIDADE APOS OUTRA REQUISICAO
# -----------------------------------------


@pytest.mark.parametrize("modelo", [Favorito, QueroOuvir])
def test_conflito_simultaneo_retorna_item_ja_existe(modelo):
    sessao = Mock(spec=Session)

    # Primeira consulta: item ainda nao existe.
    # Segunda consulta: item encontrado apos o rollback.
    sessao.scalar.side_effect = [None, 99]

    # Simula o erro ocorrido durante a gravacao.
    sessao.commit.side_effect = criar_erro_integridade()

    with patch(
        "backend.app.biblioteca.obter_ou_criar_obra",
        return_value=SimpleNamespace(id=10),
    ):
        with pytest.raises(ItemJaExiste):
            _adicionar(
                sessao=sessao,
                usuario_id=1,
                dados=OBRA_TESTE,
                modelo=modelo,
            )

    assert sessao.scalar.call_count == 2
    sessao.rollback.assert_called_once()
    sessao.refresh.assert_not_called()


# -----------------------------------------
# OUTROS ERROS DE INTEGRIDADE
# -----------------------------------------


@pytest.mark.parametrize("modelo", [Favorito, QueroOuvir])
def test_nao_confunde_outro_erro_com_duplicidade(modelo):
    sessao = Mock(spec=Session)

    # O item nao existe antes nem depois da falha.
    sessao.scalar.side_effect = [None, None]

    erro_original = criar_erro_integridade()
    sessao.commit.side_effect = erro_original

    with patch(
        "backend.app.biblioteca.obter_ou_criar_obra",
        return_value=SimpleNamespace(id=10),
    ):
        with pytest.raises(IntegrityError) as resultado:
            _adicionar(
                sessao=sessao,
                usuario_id=1,
                dados=OBRA_TESTE,
                modelo=modelo,
            )

    # O erro original deve ser preservado.
    assert resultado.value is erro_original

    assert sessao.scalar.call_count == 2
    sessao.rollback.assert_called_once()
    sessao.refresh.assert_not_called()
