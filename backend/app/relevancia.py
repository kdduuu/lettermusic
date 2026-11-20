"""Ranking deterministico, sem artistas ou albuns fixados no codigo."""
from math import log10
import unicodedata


def normalizar(texto):
    if not isinstance(texto, str):
        return ""

    decomposicao = unicodedata.normalize("NFKD", texto.casefold())
    sem_acentos = "".join(
        c for c in decomposicao if not unicodedata.combining(c)
    )

    return " ".join(
        "".join(c if c.isalnum() else " " for c in sem_acentos).split()
    )


def nivel_correspondencia(termo, titulo, artista=None):
    termo = normalizar(termo)
    titulo = normalizar(titulo)
    artista = normalizar(artista)

    if termo and termo in (titulo, artista):
        return 3

    palavras = set(termo.split())
    disponiveis = set(f"{titulo} {artista}".split())

    if palavras and palavras.issubset(disponiveis):
        return 2

    return 1


def pontuacao_musicbrainz(registro):
    try:
        valor = float(registro.get("score", 0))
        return valor if 0 <= valor <= 100 else 0
    except (TypeError, ValueError):
        return 0


def qualidade_registro(registro, categoria):
    qualidade = 0.0

    if categoria == "albuns":
        secundarios = registro.get("secondary-types") or []
        if registro.get("primary-type") == "Album" and not secundarios:
            qualidade += 2

    if categoria == "faixas":
        edicoes = registro.get("releases") or []

        if any(
            isinstance(e, dict) and e.get("status") == "Official"
            for e in edicoes
        ):
            qualidade += 2

    return qualidade


def ordenar_resultados(termo, categoria, candidatos, popularidade):
    def chave(par):
        registro, item = par

        nivel = nivel_correspondencia(
            termo, item.titulo, item.artista
        )

        ouvintes = popularidade.get(item.id_musicbrainz, 0)

        # A correspondencia textual sempre prevalece sobre a fama.
        # Entre resultados relevantes, usamos ouvintes e metadados.
        pontos = (
            pontuacao_musicbrainz(registro) / 20
            + 4 * log10(1 + ouvintes)
            + qualidade_registro(registro, categoria)
        )

        return (
            -nivel,
            -pontos,
            normalizar(item.titulo),
            item.id_musicbrainz,
        )

    return sorted(candidatos, key=chave)
