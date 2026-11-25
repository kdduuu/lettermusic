from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.app.auth import obter_usuario_atual
from backend.app.database import obter_sessao
from backend.app.favoritos_perfil import (
    AlbumFavoritoInvalido,
    UsuarioFavoritoInexistente,
    substituir_favoritos_perfil,
)
from backend.app.models import Usuario
from backend.app.schemas_perfis import AlbumFavoritoPerfil, FavoritosPerfilEntrada

router = APIRouter(tags=["Perfis Sociais"])


@router.put("/auth/perfil/favoritos", response_model=list[AlbumFavoritoPerfil])
def atualizar_favoritos_perfil(
    dados: FavoritosPerfilEntrada,
    usuario: Usuario = Depends(obter_usuario_atual),
    sessao: Session = Depends(obter_sessao),
):
    """Substitui apenas a selecao publica do usuario autenticado."""
    try:
        return substituir_favoritos_perfil(sessao, usuario.id, dados.albuns)
    except AlbumFavoritoInvalido as erro:
        raise HTTPException(status_code=422, detail=str(erro)) from erro
    except UsuarioFavoritoInexistente as erro:
        raise HTTPException(status_code=401, detail="Credenciais invalidas.") from erro
