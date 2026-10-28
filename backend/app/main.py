
import httpx

from fastapi import Depends, FastAPI, HTTPException, Path, Query
from sqlalchemy.orm import Session

from backend.app.auth import (
    autenticar_usuario,
    criar_token,
    obter_usuario_atual,
)
from backend.app.catalogo import listar_obras
from backend.app.database import obter_sessao
from backend.app.interacoes import (
    listar_escutas,
    listar_obras_ouvidas,
    marcar_obra_ouvida,
    registrar_escuta,
)
from backend.app.models import Usuario
from backend.app.musicbrainz import pesquisar_obras
from backend.app.schemas import (
    CredenciaisLogin,
    TokenAcesso,
    UsuarioCriar,
    UsuarioPublico,
)
from backend.app.schemas_interacoes import (
    EscutaPublica,
    MarcarOuvidaEntrada,
    ObraOuvidaPublica,
    RegistrarEscutaEntrada,
)
from backend.app.usuarios import (
    UsuarioJaExiste,
    buscar_usuario_por_username,
    cadastrar_usuario,
)


app = FastAPI(title="Lettermusic API")


@app.get("/health")
def verificar_saude():
    """Confirma que a API esta respondendo."""
    return {"status": "ok"}


@app.get("/catalogo/buscar")
def buscar_obras(
    termo: str = Query(min_length=2, max_length=100),
    artista: str | None = Query(default=None, min_length=2, max_length=100),
):
    try:
        obras = pesquisar_obras(termo, artista)

    except httpx.HTTPError as erro:
        raise HTTPException(
            status_code=502,
            detail="Nao foi possivel consultar o MusicBrainz.",
        ) from erro

    return {"resultados": obras}


@app.get("/catalogo/obras")
def consultar_catalogo(sessao: Session = Depends(obter_sessao)):
    obras = listar_obras(sessao)

    return {
        "resultados": [
            {
                "id": obra.id,
                "id_musicbrainz": obra.id_musicbrainz,
                "titulo": obra.titulo,
                "artista": obra.artista,
                "tipo": obra.tipo,
                "data_lancamento": obra.data_lancamento,
            }
            for obra in obras
        ]
    }


@app.post("/usuarios", response_model=UsuarioPublico, status_code=201)
def criar_usuario(
    dados: UsuarioCriar,
    sessao: Session = Depends(obter_sessao),
):
    try:
        return cadastrar_usuario(sessao, dados)
    except UsuarioJaExiste:
        raise HTTPException(
            status_code=409,
            detail="Username ou e-mail indisponivel.",
        ) from None


@app.get("/usuarios/{username}", response_model=UsuarioPublico)
def consultar_perfil(
    username: str = Path(
        min_length=3,
        max_length=30,
        pattern=r"^[a-zA-Z0-9_]+$",
    ),
    sessao: Session = Depends(obter_sessao),
):
    usuario = buscar_usuario_por_username(sessao, username)

    if usuario is None:
        raise HTTPException(
            status_code=404,
            detail="Usuario nao encontrado.",
        )

    return usuario


@app.post("/auth/login", response_model=TokenAcesso)
def fazer_login(
    dados: CredenciaisLogin,
    sessao: Session = Depends(obter_sessao),
):
    usuario = autenticar_usuario(
        sessao,
        dados.identificador,
        dados.senha,
    )

    return {
        "access_token": criar_token(usuario.id),
        "token_type": "bearer",
    }


@app.get("/auth/me", response_model=UsuarioPublico)
def minha_conta(usuario: Usuario = Depends(obter_usuario_atual)):
    return usuario


# --------------------------------------------------
# SPRINT 03 - OBRAS OUVIDAS
# --------------------------------------------------


@app.post(
    "/interacoes/obras-ouvidas",
    response_model=ObraOuvidaPublica,
)
def marcar_como_ouvida(
    dados: MarcarOuvidaEntrada,
    usuario: Usuario = Depends(obter_usuario_atual),
    sessao: Session = Depends(obter_sessao),
):
    return marcar_obra_ouvida(
        sessao,
        usuario.id,
        dados,
    )


@app.get(
    "/interacoes/obras-ouvidas",
    response_model=list[ObraOuvidaPublica],
)
def consultar_obras_ouvidas(
    usuario: Usuario = Depends(obter_usuario_atual),
    sessao: Session = Depends(obter_sessao),
):
    return listar_obras_ouvidas(
        sessao,
        usuario.id,
    )


# --------------------------------------------------
# SPRINT 03 - HISTORICO DE ESCUTAS
# --------------------------------------------------


@app.post(
    "/interacoes/escutas",
    response_model=EscutaPublica,
    status_code=201,
)
def criar_registro_escuta(
    dados: RegistrarEscutaEntrada,
    usuario: Usuario = Depends(obter_usuario_atual),
    sessao: Session = Depends(obter_sessao),
):
    return registrar_escuta(
        sessao,
        usuario.id,
        dados,
    )


@app.get(
    "/interacoes/escutas",
    response_model=list[EscutaPublica],
)
def consultar_historico_escutas(
    usuario: Usuario = Depends(obter_usuario_atual),
    sessao: Session = Depends(obter_sessao),
):
    return listar_escutas(
        sessao,
        usuario.id,
    )
