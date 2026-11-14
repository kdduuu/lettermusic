// Módulo de acesso à API executado no servidor Next.js.
// Não importar em Client Components.
export type ObraMusical = {
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