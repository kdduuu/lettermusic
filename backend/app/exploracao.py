"""Consultas externas sem persistencia, reutilizando o cliente MusicBrainz."""
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field

from backend.app import musicbrainz as mb

BASE = "https://musicbrainz.org/ws/2/"
Categoria = Literal["albuns", "artistas", "faixas"]


class LancamentoRelacionado(BaseModel):
    id_musicbrainz: str
    titulo: str


class ItemExploracao(BaseModel):
    id_musicbrainz: str
    titulo: str
    artista: str | None = None
    tipo: str | None = None
    data: str | None = None
    subtitulo: str | None = None
    relacionados: list[LancamentoRelacionado] = Field(default_factory=list)


class PaginaExploracao(BaseModel):
    resultados: list[ItemExploracao]
    pagina: int
    tem_proxima: bool


class FaixaEdicao(BaseModel):
    disco: int
    numero: str
    titulo: str
    duracao_ms: int | None = None


class FaixasAlbum(BaseModel):
    edicao_id: str | None = None
    edicao: str | None = None
    data: str | None = None
    pais: str | None = None
    faixas: list[FaixaEdicao] = Field(default_factory=list)


def identificador(valor):
    return str(UUID(str(valor)))


def texto(valor):
    return valor if isinstance(valor, str) and valor.strip() else None


def objeto(valor):
    if not isinstance(valor, dict):
        raise ValueError("Resposta inesperada do MusicBrainz.")
    return valor


def registros(dados, chave):
    itens = objeto(dados).get(chave)
    if not isinstance(itens, list):
        raise ValueError("Lista MusicBrainz invalida.")
    return [objeto(item) for item in itens]


def consulta_textual(termo: str, campos: tuple[str, ...]) -> str:
    # O usuario fornece texto, nunca uma expressao Lucene arbitraria.
    palavras = termo.split()
    if not palavras:
        raise ValueError("Pesquisa vazia.")

    grupos = []
    for palavra in palavras:
        segura = mb.escapar_consulta(palavra)
        grupos.append("(" + " OR ".join(
            f'{campo}:"{segura}"' for campo in campos
        ) + ")")
    return " AND ".join(grupos)


def converter_album(dados):
    return ItemExploracao(
        id_musicbrainz=identificador(dados.get("id")),
        titulo=dados["title"],
        artista=mb.extrair_artista(dados.get("artist-credit", [])),
        tipo=texto(dados.get("primary-type")),
        data=texto(dados.get("first-release-date")),
    )


def converter_artista(dados):
    area = dados.get("area")
    local = texto(area.get("name")) if isinstance(area, dict) else None

    subtitulo = " · ".join(filter(None, [
        local or texto(dados.get("country")),
        texto(dados.get("disambiguation")),
    ]))

    return ItemExploracao(
        id_musicbrainz=identificador(dados.get("id")),
        titulo=dados["name"],
        tipo=texto(dados.get("type")),
        subtitulo=subtitulo or None,
    )


def converter_faixa(dados):
    relacionados = {}

    for edicao in dados.get("releases") or []:
        grupo = edicao.get("release-group")
        if not isinstance(grupo, dict) or not grupo.get("id"):
            continue

        mbid = identificador(grupo["id"])
        titulo = texto(grupo.get("title")) or texto(edicao.get("title"))
        if titulo and mbid not in relacionados:
            relacionados[mbid] = LancamentoRelacionado(
                id_musicbrainz=mbid, titulo=titulo,
            )

    return ItemExploracao(
        id_musicbrainz=identificador(dados.get("id")),
        titulo=dados["title"],
        artista=mb.extrair_artista(dados.get("artist-credit", [])),
        tipo="Faixa",
        relacionados=list(relacionados.values())[:8],
    )


def interpretar_pagina(dados, chave, conversor, pagina, limite, total_chave):
    linhas = registros(dados, chave)
    total = dados.get(total_chave)

    if type(total) is not int or total < 0:
        raise ValueError("Contagem MusicBrainz invalida.")

    offset = (pagina - 1) * limite

    return PaginaExploracao(
        resultados=[conversor(item) for item in linhas],
        pagina=pagina,
        tem_proxima=offset + len(linhas) < total and bool(linhas),
    )


def pesquisar(termo: str, categoria: Categoria, pagina: int, limite: int):
    configuracoes = {
        "albuns": (
            "release-group", "release-groups",
            ("releasegroup", "artistname"), converter_album,
        ),
        "artistas": (
            "artist", "artists",
            ("artist", "alias"), converter_artista,
        ),
        "faixas": (
            "recording", "recordings",
            ("recording", "artistname"), converter_faixa,
        ),
    }

    entidade, chave, campos, conversor = configuracoes[categoria]
    parametros = {
        "query": consulta_textual(termo, campos),
        "fmt": "json",
        "limit": limite,
        "offset": (pagina - 1) * limite,
    }

    return mb._consultar(
        BASE + entidade + "/", parametros, "busca", mb.TTL_BUSCA,
        lambda dados: interpretar_pagina(
            dados, chave, conversor, pagina, limite, "count"
        ),
    )


def consultar_artista(mbid: str):
    def interpretar(dados):
        item = converter_artista(objeto(dados))
        if item.id_musicbrainz != mbid:
            raise ValueError("Artista diferente do solicitado.")
        return item

    return mb._consultar(
        BASE + "artist/" + mbid,
        {"fmt": "json"},
        "detalhe", mb.TTL_DETALHE, interpretar,
    )


def consultar_discografia(mbid: str, pagina: int, limite: int):
    return mb._consultar(
        BASE + "release-group/",
        {
            "artist": mbid,
            "fmt": "json",
            "inc": "artist-credits",
            "limit": limite,
            "offset": (pagina - 1) * limite,
        },
        "busca", mb.TTL_DETALHE,
        lambda dados: interpretar_pagina(
            dados, "release-groups", converter_album,
            pagina, limite, "release-group-count",
        ),
    )


def interpretar_faixas(dados):
    edicoes = registros(dados, "releases")
    if not edicoes:
        return FaixasAlbum()

    edicao = edicoes[0]
    faixas = []

    for indice, disco in enumerate(edicao.get("media") or [], start=1):
        for posicao, faixa in enumerate(disco.get("tracks") or [], start=1):
            gravacao = faixa.get("recording") or {}
            titulo = texto(faixa.get("title")) or texto(gravacao.get("title"))
            if not titulo:
                continue

            duracao = faixa.get("length")
            if type(duracao) is not int or duracao < 0:
                duracao = None

            faixas.append(FaixaEdicao(
                disco=indice,
                numero=str(faixa.get("number") or posicao),
                titulo=titulo,
                duracao_ms=duracao,
            ))

    return FaixasAlbum(
        edicao_id=identificador(edicao["id"]),
        edicao=edicao["title"],
        data=texto(edicao.get("date")),
        pais=texto(edicao.get("country")),
        faixas=faixas,
    )


def consultar_faixas(mbid: str):
    # Uma edicao oficial, identificada na resposta.
    # Nao pressupoe que seja a edicao original.
    return mb._consultar(
        BASE + "release/",
        {
            "release-group": mbid,
            "status": "official",
            "inc": "recordings",
            "limit": 1,
            "fmt": "json",
        },
        "busca", mb.TTL_DETALHE, interpretar_faixas,
    )
