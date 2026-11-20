// Módulo de acesso à API executado no servidor Next.js.
// Não importar em Client Components.
export type CreditoArtista = {
  id_musicbrainz: string | null;
  nome: string;
  separador: string;
};

export type ObraMusical = {
  creditos_artistas?: CreditoArtista[];
  id_musicbrainz: string | null;
  titulo: string | null;
  artista: string | null;
  tipo: string | null;
  data_lancamento: string | null;
};

type ResultadoBusca =
  | { ok: true; obras: ObraMusical[] }
  | { ok: false; mensagem: string };

type ResultadoDetalhe =
  | { ok: true; obra: ObraMusical }
  | { ok: false; status: number; mensagem: string };

function stringOuNull(valor: unknown): string | null {
  return typeof valor === "string" ? valor : null;
}

function converterObra(item: Record<string, unknown>): ObraMusical {
  return {
    id_musicbrainz: stringOuNull(item.id_musicbrainz),
    titulo: stringOuNull(item.titulo),
    artista: stringOuNull(item.artista),
    tipo: stringOuNull(item.tipo),
    data_lancamento: stringOuNull(item.data_lancamento),
    creditos_artistas: Array.isArray(item.creditos_artistas)
      ? item.creditos_artistas.filter(
          (c: unknown): c is CreditoArtista =>
            objeto(c) && typeof c.nome === "string" &&
            typeof c.separador === "string" &&
            (c.id_musicbrainz === null ||
              (typeof c.id_musicbrainz === "string" &&
                /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i.test(c.id_musicbrainz)))
        )
      : [],
  };
}

function objeto(valor: unknown): valor is Record<string, unknown> {
  return typeof valor === "object" && valor !== null && !Array.isArray(valor);
}

function urlBackend(): string {
  return (process.env.BACKEND_URL ?? "http://127.0.0.1:8000").replace(/\/$/, "");
}

export async function pesquisarAlbuns(termo: string): Promise<ResultadoBusca> {
  const parametros = new URLSearchParams({ termo });

  try {
    const resposta = await fetch(
      `${urlBackend()}/catalogo/buscar?${parametros.toString()}`,
      { cache: "no-store", signal: AbortSignal.timeout(20_000) },
    );

    if (!resposta.ok) {
      return {
        ok: false,
        mensagem:
          resposta.status === 502
            ? "O catálogo musical está temporariamente indisponível."
            : "Não foi possível consultar o catálogo agora.",
      };
    }

    const dados: unknown = await resposta.json();
    if (!objeto(dados) || !Array.isArray(dados.resultados)) {
      return { ok: false, mensagem: "Resposta inesperada do catálogo." };
    }

    const obras = dados.resultados.filter(objeto).map(converterObra);
    return { ok: true, obras };
  } catch {
    return {
      ok: false,
      mensagem: "Não foi possível conectar ao catálogo. Verifique se a API está ligada.",
    };
  }
}

export async function detalharAlbum(idMusicBrainz: string): Promise<ResultadoDetalhe> {
  // O servidor também valida o formato, evitando consultas desnecessárias.
  const idValido = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;
  if (!idValido.test(idMusicBrainz)) {
    return { ok: false, status: 422, mensagem: "Identificador do álbum inválido." };
  }

  try {
    const resposta = await fetch(
      `${urlBackend()}/catalogo/musicbrainz/${encodeURIComponent(idMusicBrainz)}`,
      { cache: "no-store", signal: AbortSignal.timeout(20_000) },
    );

    if (!resposta.ok) {
      return {
        ok: false,
        status: resposta.status,
        mensagem:
          resposta.status === 404
            ? "Álbum não encontrado."
            : resposta.status === 502
              ? "O MusicBrainz está temporariamente indisponível."
              : "Não foi possível consultar os detalhes do álbum.",
      };
    }

    const dados: unknown = await resposta.json();
    if (!objeto(dados) || typeof dados.id_musicbrainz !== "string" ||
        typeof dados.titulo !== "string" || !dados.titulo.trim()) {
      return { ok: false, status: 502, mensagem: "Dados inesperados do catálogo." };
    }

    return { ok: true, obra: converterObra(dados) };
  } catch {
    return {
      ok: false,
      status: 503,
      mensagem: "Não foi possível conectar ao catálogo. Verifique se a API está ligada.",
    };
  }
}

export async function obterCapaAlbum(idMusicBrainz: string): Promise<string | null> {
  const idValido = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;
  if (!idValido.test(idMusicBrainz)) return null;

  try {
    const resposta = await fetch(
      `${urlBackend()}/catalogo/musicbrainz/${encodeURIComponent(idMusicBrainz)}/capa`,
      { cache: "no-store", signal: AbortSignal.timeout(10_000) },
    );
    if (!resposta.ok) return null;

    const dados: unknown = await resposta.json();
    if (!objeto(dados) || typeof dados.url !== "string") return null;

    // A URL deve ter sido construída pelo nosso back-end, no domínio esperado.
    const url = new URL(dados.url);
    if (
      url.protocol !== "https:" ||
      url.hostname !== "coverartarchive.org" ||
      url.pathname !== `/release-group/${idMusicBrainz.toLowerCase()}/front-500` ||
      url.search !== "" ||
      url.hash !== ""
    ) {
      return null;
    }
    return url.toString();
  } catch {
    // Capa é opcional: falha externa não impede a visualização do álbum.
    return null;
  }
}