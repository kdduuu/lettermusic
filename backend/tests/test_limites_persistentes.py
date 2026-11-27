import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from backend.app.limites_persistentes import (
    LimiteExcedido,
    RegraLimite,
    chave_limite,
    limpar_expirados,
    reservar,
)
from backend.app.models import LimiteRequisicao


@pytest.fixture
def motor(tmp_path):
    url = f"sqlite+pysqlite:///{tmp_path / 'limites.db'}"
    motor = create_engine(url)
    LimiteRequisicao.__table__.create(motor)
    yield motor
    motor.dispose()


def test_limite_persiste_entre_motores_e_expira(motor):
    regra = RegraLimite("a" * 64, 2, 60)
    reservar(motor, [regra], agora=100)
    outro_motor = create_engine(motor.url)
    try:
        reservar(outro_motor, [regra], agora=101)
        with pytest.raises(LimiteExcedido) as erro:
            reservar(outro_motor, [regra], agora=102)
        assert erro.value.aguardar == 58
        reservar(outro_motor, [regra], agora=160)
        with Session(motor) as sessao:
            registro = sessao.get(LimiteRequisicao, regra.chave)
            assert registro.quantidade == 1
            assert registro.expira_em == 220
    finally:
        outro_motor.dispose()


def test_bloqueio_reverte_todas_as_reservas(motor):
    livre = RegraLimite("a" * 64, 5, 60)
    bloqueada = RegraLimite("b" * 64, 1, 60)
    reservar(motor, [bloqueada], agora=100)
    with pytest.raises(LimiteExcedido):
        reservar(motor, [bloqueada, livre], agora=101)
    with Session(motor) as sessao:
        assert sessao.get(LimiteRequisicao, livre.chave) is None
        assert sessao.get(LimiteRequisicao, bloqueada.chave).quantidade == 1


def test_limpeza_remove_somente_expirados(motor):
    a = RegraLimite("a" * 64, 2, 10)
    b = RegraLimite("b" * 64, 2, 60)
    reservar(motor, [a, b], agora=100)
    assert limpar_expirados(motor, agora=110) == 1
    with Session(motor) as sessao:
        assert sessao.scalars(select(LimiteRequisicao.chave)).all() == [b.chave]


def test_chaves_separam_escopos_e_segredos():
    chave = chave_limite("login", "192.0.2.1", "segredo-teste")
    assert len(chave) == 64
    assert chave == chave_limite("login", "192.0.2.1", "segredo-teste")
    assert chave != chave_limite("cadastro", "192.0.2.1", "segredo-teste")
    assert chave != chave_limite("login", "192.0.2.1", "outro-segredo")


def test_rejeita_regras_duplicadas_e_invalidas(motor):
    regra = RegraLimite("a" * 64, 1, 60)
    for regras in ([], [regra, regra], [RegraLimite("ip", 1, 60)],
                   [RegraLimite("b" * 64, 0, 60)]):
        with pytest.raises(ValueError):
            reservar(motor, regras, agora=100)
