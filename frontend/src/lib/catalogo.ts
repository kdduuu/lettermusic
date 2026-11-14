// Comunicação servidor Next.js -> API FastAPI. Não importar em Client Components.
export type ObraMusical = {
  id_musicbrainz: string | null;
  titulo: string | null;
  artista: string | null;
  tipo: string | null;
  data_lancamento: string | null;
};

type Resultado =
  | { ok: true; obras: ObraMusical[] }
  | { ok: false; mensagem: string };

function stringOuNull(valor: unknown): string | null {
  return typeof valor === "string" ? valor : null;
}

export async function pesquisarAlbuns(termo: string): Promise<Resultado> {
  const backend = (process.env.BACKEND_URL ?? "http://127.0.0.1:8000")
    .replace(/\/$/, "");
  const parametros = new URLSearchParams({ termo });

  try {
    const resposta = await fetch(
      `${backend}/catalogo/buscar?${parametros.toString()}`,
      {
        cache: "no-store",
        signal: AbortSignal.timeout(20_000),
      },
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
    if (
      typeof dados !== "object" ||
      dados === null ||
      !("resultados" in dados) ||
      !Array.isArray(dados.resultados)
    ) {
      return { ok: false, mensagem: "Resposta inesperada do catálogo." };
    }

    const obras: ObraMusical[] = dados.resultados
      .filter(
        (item: unknown): item is Record<string, unknown> =>
          typeof item === "object" && item !== null && !Array.isArray(item),
      )
      .map((item: Record<string, unknown>) => ({
        id_musicbrainz: stringOuNull(item.id_musicbrainz),
        titulo: stringOuNull(item.titulo),
        artista: stringOuNull(item.artista),
        tipo: stringOuNull(item.tipo),
        data_lancamento: stringOuNull(item.data_lancamento),
      }));

    return { ok: true, obras };
  } catch {
    // A mensagem pública não expõe detalhes internos da conexão.
    return {
      ok: false,
      mensagem:
        "Não foi possível conectar ao catálogo. Verifique se a API está ligada.",
    };
  }
}