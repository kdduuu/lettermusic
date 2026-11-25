"""Consultas externas sem persistencia, reutilizando o cliente MusicBrainz."""
from typing import Literal
from uuid import UUID

import httpx
from pydantic import BaseModel, Field

from backend.app import musicbrainz as mb
from backend.app.popularidade import obter_popularidade, obter_destaques
from backend.app.relevancia import ordenar_resultados

BASE = "https://musicbrainz.org/ws/2/"
Categoria = Literal["albuns", "artistas", "faixas"]
TipoDiscografia = Literal[
    "todos", "album", "single", "ep", "compilation", "live"
]
MAX_CANDIDATOS = 60
OrdemDiscografia = Literal["catalogo", "antigos", "recentes"]
MAX_DISCOGRAFIA_ORDENADA = 500
LOTE_DISCOGRAFIA = 100


class DiscografiaExtensa(Exception):
    """Evita ordenar parcialmente um catalogo acima do limite seguro."""



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
    palavras = termo.split()
    if not palavras:
        raise ValueError("Pesquisa vazia.")

    grupos = []

    for palavra in palavras:
        segura = mb.escapar_consulta(palavra)
        alternativas = [
            f'{campo}:"{segura}"^3' for campo in campos
        ]

        # Busca aproximada somente para palavras suficientemente longas.
        # Nao permite que operadores fornecidos pelo usuario virem filtros.
        if len(palavra) >= 5 and palavra.isalnum():
            alternativas.extend(
                f"{campo}:{palavra}~1" for campo in campos
            )

        grupos.append("(" + " OR ".join(alternativas) + ")")

    return " AND ".join(grupos)


def converter_album(dados):
    secundarios = dados.get("secondary-types") or []
    subtitulo = " · ".join(
        tipo for tipo in secundarios if isinstance(tipo, str)
    )
    return ItemExploracao(
        id_musicbrainz=identificador(dados.get("id")),
        titulo=dados["title"],
        artista=mb.extrair_artista(dados.get("artist-credit", [])),
        tipo=texto(dados.get("primary-type")),
        data=texto(dados.get("first-release-date")),
        subtitulo=subtitulo or None,
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


def enriquecer_faixas(itens):
    """Busca lancamentos relacionados em lote pelo ID das gravacoes."""
    if not itens:
        return itens

    ids = {item.id_musicbrainz for item in itens}

    query = " OR ".join(
        f'rid:"{identificador_}"'
        for identificador_ in sorted(ids)
    )

    try:
        linhas = mb._consultar(
            BASE + "recording/",
            {
                "query": query,
                "fmt": "json",
                "limit": len(ids),
                "offset": 0,
            },
            "busca",
            mb.TTL_DETALHE,
            lambda dados: registros(dados, "recordings"),
        )
    except (httpx.HTTPError, ValueError, TypeError, KeyError, AttributeError):
        return itens

    relacionados = {}

    for linha in linhas:
        try:
            item = converter_faixa(linha)
        except (ValueError, TypeError, KeyError, AttributeError):
            continue

        if item.id_musicbrainz in ids:
            relacionados[item.id_musicbrainz] = item.relacionados

    return [
        item.model_copy(update={
            "relacionados": relacionados.get(item.id_musicbrainz, [])
        })
        for item in itens
    ]


def pagina_destaques(artista_id, categoria, pagina, limite):
    destaques = obter_destaques(categoria, artista_id)

    if not destaques:
        return None

    offset = (pagina - 1) * limite
    recorte = destaques[offset:offset + limite]

    itens = [
        ItemExploracao(
            id_musicbrainz=item["id_musicbrainz"],
            titulo=item["titulo"],
            artista=item.get("artista"),
            tipo=item.get("tipo"),
            data=item.get("data"),
        )
        for item in recorte
    ]

    # A previa de 3 faixas usa os dados ja retornados pelo
    # ListenBrainz, sem consultar o MusicBrainz novamente.
    # Na pagina completa, mantemos os lancamentos associados.
    if categoria == "faixas" and limite > 3:
        itens = enriquecer_faixas(itens)

    return PaginaExploracao(
        resultados=itens,
        pagina=pagina,
        tem_proxima=offset + len(recorte) < len(destaques),
    )


def pesquisar(
    termo: str,
    categoria: Categoria,
    pagina: int,
    limite: int,
    artista_id: str | None = None,
):
    if artista_id and categoria != "artistas":
        artista_id = identificador(artista_id)

        destaques = pagina_destaques(
            artista_id, categoria, pagina, limite
        )

        if destaques is not None:
            return destaques
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
    termo = " ".join(termo.split())
    query = consulta_textual(termo, campos)

    if categoria != "artistas":
        # Bonus para resultados associados a lancamentos oficiais,
        # sem eliminar completamente o restante do catalogo.
        query = f"+({query}) status:official^2"

    if artista_id and categoria != "artistas":
        # Fallback: o termo pode estar incorreto, mas o MBID nao e ambiguo.
        query = f'+(arid:"{artista_id}") status:official^2'

        if categoria == "albuns":
            query += " primarytype:album^3"

    parametros = {
        "query": query,
        "fmt": "json",
        "limit": MAX_CANDIDATOS,
        "offset": 0,
    }

    def interpretar(dados):
        linhas = registros(dados, chave)
        total = dados.get("count")

        if type(total) is not int or total < 0:
            raise ValueError("Contagem MusicBrainz invalida.")

        return linhas[:MAX_CANDIDATOS]

    # Mesma consulta para a previa e para as paginas individuais.
    # Isto preserva o cache e evita reordenar cada pagina isoladamente.
    linhas = mb._consultar(
        BASE + entidade + "/", parametros, "busca",
        mb.TTL_BUSCA, interpretar,
    )

    candidatos = []
    ids = set()

    for linha in linhas:
        try:
            item = conversor(linha)
        except (ValueError, TypeError, KeyError, AttributeError):
            continue

        if item.id_musicbrainz not in ids:
            ids.add(item.id_musicbrainz)
            candidatos.append((linha, item))

    # Consulta opcional fora do lock de rede do MusicBrainz.
    # Nao chamar novamente o provedor opcional durante o fallback.
    popularidade = (
        {} if artista_id
        else obter_popularidade(categoria, list(ids))
    )

    ordenados = ordenar_resultados(
        termo, categoria, candidatos, popularidade
    )

    offset = (pagina - 1) * limite
    recorte = ordenados[offset:offset + limite]

    return PaginaExploracao(
        resultados=[item for _, item in recorte],
        pagina=pagina,
        tem_proxima=offset + len(recorte) < len(ordenados),
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


def consultar_discografia(
    mbid: str,
    pagina: int,
    limite: int,
    tipo: TipoDiscografia = "todos",
    ordem: OrdemDiscografia = "catalogo",
):
    if ordem != "catalogo":
        return ordenar_discografia(mbid, pagina, limite, tipo, ordem)

    parametros = {
        "artist": mbid,
        "fmt": "json",
        "inc": "artist-credits",
        "limit": limite,
        "offset": (pagina - 1) * limite,
        "release-group-status": "website-default",
    }

    if tipo != "todos":
        parametros["type"] = tipo

    return mb._consultar(
        BASE + "release-group/",
        parametros,
        "busca", mb.TTL_DETALHE,
        lambda dados: interpretar_pagina(
            dados, "release-groups", converter_album,
            pagina, limite, "release-group-count",
        ),
    )


def ordenar_discografia(
    mbid: str, pagina: int, limite: int, tipo: TipoDiscografia,
    ordem: OrdemDiscografia,
) -> PaginaExploracao:
    """Ordena a colecao filtrada inteira antes de paginar; nao persiste obras."""
    parametros = {
        "artist": mbid, "fmt": "json", "inc": "artist-credits",
        "limit": LOTE_DISCOGRAFIA, "release-group-status": "website-default",
    }
    if tipo != "todos":
        parametros["type"] = tipo

    def interpretar(dados):
        linhas = registros(dados, "release-groups")
        total = dados.get("release-group-count")
        if type(total) is not int or total < 0:
            raise ValueError("Contagem MusicBrainz invalida.")
        return total, [converter_album(item) for item in linhas]

    itens = {}
    offset = 0
    total_esperado = None
    while total_esperado is None or offset < total_esperado:
        total, lote = mb._consultar(
            BASE + "release-group/", {**parametros, "offset": offset},
            "busca", mb.TTL_DETALHE, interpretar,
        )
        if total > MAX_DISCOGRAFIA_ORDENADA:
            raise DiscografiaExtensa()
        if total_esperado is None:
            total_esperado = total
        if total != total_esperado or len(lote) != min(LOTE_DISCOGRAFIA, total - offset):
            raise ValueError("Discografia alterada durante a consulta.")
        for item in lote:
            if item.id_musicbrainz in itens:
                raise ValueError("Discografia retornou registros duplicados.")
            itens[item.id_musicbrainz] = item
        offset += len(lote)

    # Datas parciais do MusicBrainz (YYYY, YYYY-MM, YYYY-MM-DD)
    # mantem a precisao original. Desconhecidas ficam ao final em ambas as ordens.
    conhecidos = [item for item in itens.values() if item.data]
    desconhecidos = [item for item in itens.values() if not item.data]
    desempate = lambda item: (item.titulo.casefold(), item.id_musicbrainz)
    conhecidos.sort(key=desempate)
    conhecidos.sort(key=lambda item: item.data or "", reverse=ordem == "recentes")
    desconhecidos.sort(key=desempate)
    ordenados = conhecidos + desconhecidos
    inicio = (pagina - 1) * limite
    recorte = ordenados[inicio:inicio + limite]
    return PaginaExploracao(
        resultados=recorte, pagina=pagina,
        tem_proxima=inicio + len(recorte) < len(ordenados) and bool(recorte),
    )


def interpretar_edicao(edicao):
    faixas = []

    for indice, disco in enumerate(edicao.get("media") or [], start=1):
        for posicao, faixa in enumerate(disco.get("tracks") or [], start=1):
            gravacao = faixa.get("recording") or {}
            titulo = texto(faixa.get("title"))
            desconhecidos = {"[unknown]", "unknown", "[untitled]"}
            if not titulo or titulo.casefold() in desconhecidos:
                titulo = texto(gravacao.get("title"))
            if not titulo or titulo.casefold() in desconhecidos:
                titulo = "Faixa sem título informado"

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


def interpretar_faixas(dados):
    edicoes = registros(dados, "releases")
    candidatas = []

    for edicao in edicoes:
        try:
            candidatas.append(interpretar_edicao(edicao))
        except (ValueError, TypeError, KeyError, AttributeError):
            continue

    if not candidatas:
        return FaixasAlbum()

    def qualidade(edicao):
        desconhecidas = sum(
            faixa.titulo == "Faixa sem título informado"
            for faixa in edicao.faixas
        )
        proporcao = desconhecidas / max(1, len(edicao.faixas))

        return (
            not bool(edicao.faixas),
            proporcao,
            edicao.data is None,
            edicao.data or "9999",
            edicao.edicao_id or "",
        )

    return min(candidatas, key=qualidade)


def consultar_faixas(mbid: str):
    # Seleciona uma edicao entre ate cinco candidatas oficiais.
    # Prefere dados completos e datas mais antigas, sem afirmar
    # que a escolhida seja necessariamente a edicao original.
    return mb._consultar(
        BASE + "release/",
        {
            "release-group": mbid,
            "status": "official",
            "inc": "recordings",
            "limit": 5,
            "fmt": "json",
        },
        "busca", mb.TTL_DETALHE, interpretar_faixas,
    )
