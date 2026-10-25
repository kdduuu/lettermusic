
import httpx

from fastapi import Depends, FastAPI, HTTPException, Query
from sqlalchemy.orm import Session

from backend.app.auth import (
    autenticar_usuario,
    criar_token,
    obter_usuario_atual
)
from backend.app.catalogo import listar_obras
from backend.app.database import obter_sessao
from backend.app.models import Usuario
from backend.app.musicbrainz import pesquisar_obras
from backend.app.schemas import (
    CredenciaisLogin,
    TokenAcesso,
    UsuarioCriar,
    UsuarioPublico
)
from backend.app.usuarios import UsuarioJaExiste, cadastrar_usuario


app = FastAPI(title="Lettermusic API")


@app.get("/health")
def verificar_saude():
    """Confirma que a API está respondendo."""
    return {"status": "ok"}


@app.get("/catalogo/buscar")
def buscar_obras(
    termo: str = Query(min_length=2, max_length=100),
    artista: str | None = Query(default=None, min_length=2, max_length=100)
):
    try:
        obras = pesquisar_obras(termo, artista)

    except httpx.HTTPError as erro:
        raise HTTPException(
            status_code=502,
            detail="Nao foi possivel consultar o MusicBrainz."
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
                "tipo": obra.tipo,
                "data_lancamento": obra.data_lancamento
            }
            for obra in obras
        ]
    }


@app.post("/usuarios", response_model=UsuarioPublico, status_code=201)
def criar_usuario(
    dados: UsuarioCriar,
    sessao: Session = Depends(obter_sessao)
):
    try:
        return cadastrar_usuario(sessao, dados)
    except UsuarioJaExiste:
        raise HTTPException(
            status_code=409,
            detail="Username ou e-mail indisponivel."
        ) from None


@app.post("/auth/login", response_model=TokenAcesso)
def fazer_login(
    dados: CredenciaisLogin,
    sessao: Session = Depends(obter_sessao)
):
    usuario = autenticar_usuario(
        sessao,
        dados.identificador,
        dados.senha
    )

    return {
        "access_token": criar_token(usuario.id),
        "token_type": "bearer"
    }


@app.get("/auth/me", response_model=UsuarioPublico)
def minha_conta(usuario: Usuario = Depends(obter_usuario_atual)):
    return usuario
