import { requisitarBackend } from "@/lib/backend";
import { MBID_VALIDO } from "@/lib/estado-album";

export type Categoria = "albuns" | "artistas" | "faixas";

export type Item = {
  id_musicbrainz: string;
  titulo: string;
  artista: string | null;
  tipo: string | null;
  data: string | null;
  subtitulo: string | null;
  relacionados: { id_musicbrainz: string; titulo: string }[];
};

export type Pagina = {
  resultados: Item[];
  pagina: number;
  tem_proxima: boolean;
};

type Faixas = {
  edicao_id: string | null;
  edicao: string | null;
  data: string | null;
  pais: string | null;
  faixas: {
    disco: number;
    numero: string;
    titulo: string;
    duracao_ms: number | null;
  }[];
};

type Resultado<T> =
  | { ok: true; dados: T }
  | { ok: false; mensagem: string };

function objeto(v: unknown): v is Record<string, unknown> {
  return typeof v === "object" && v !== null && !Array.isArray(v);
}

function texto(v: unknown) {
  return v === null || typeof v === "string";
}

function mbid(v: unknown) {
  return typeof v === "string" && MBID_VALIDO.test(v);
}

function itemValido(v: unknown): v is Item {
  return objeto(v) && mbid(v.id_musicbrainz) &&
    typeof v.titulo === "string" && texto(v.artista) &&
    texto(v.tipo) && texto(v.data) && texto(v.subtitulo) &&
    Array.isArray(v.relacionados) &&
    v.relacionados.every((r: unknown) =>
      objeto(r) && mbid(r.id_musicbrainz) && typeof r.titulo === "string"
    );
}

function paginaValida(v: unknown): v is Pagina {
  return objeto(v) && typeof v.pagina === "number" &&
    Number.isSafeInteger(v.pagina) && v.pagina >= 1 &&
    typeof v.tem_proxima === "boolean" &&
    Array.isArray(v.resultados) && v.resultados.every(itemValido);
}

function faixasValidas(v: unknown): v is Faixas {
  return objeto(v) &&
    (v.edicao_id === null || mbid(v.edicao_id)) &&
    texto(v.edicao) && texto(v.data) && texto(v.pais) &&
    Array.isArray(v.faixas) && v.faixas.every((f: unknown) =>
      objeto(f) && typeof f.disco === "number" &&
      Number.isSafeInteger(f.disco) && f.disco > 0 &&
      typeof f.numero === "string" && typeof f.titulo === "string" &&
      (f.duracao_ms === null ||
        (typeof f.duracao_ms === "number" &&
          Number.isSafeInteger(f.duracao_ms) && f.duracao_ms >= 0))
    );
}

async function consultar<T>(
  caminho: string,
  validar: (v: unknown) => v is T,
): Promise<Resultado<T>> {
  try {
    const resposta = await requisitarBackend(`/catalogo/explorar${caminho}`);
    if (!resposta.ok) return {
      ok: false,
      mensagem: resposta.status === 404
        ? "Record not found."
        : "Search temporarily unavailable.",
    };

    const dados: unknown = await resposta.json();
    if (!validar(dados)) return {
      ok: false, mensagem: "Unexpected catalog response.",
    };

    return { ok: true, dados };
  } catch {
    return { ok: false, mensagem: "Unable to connect to the catalog." };
  }
}

export function obterPagina(valor: string | string[] | undefined) {
  const n = typeof valor === "string" && /^\d+$/.test(valor) ? Number(valor) : 1;
  return Number.isSafeInteger(n) && n >= 1 && n <= 1000 ? n : 1;
}

export function buscar(
  termo: string,
  categoria: Categoria,
  pagina = 1,
  limite = 12,
  artistaId?: string,
) {
  const params = new URLSearchParams({
    termo, categoria, pagina: String(pagina), limite: String(limite),
  });

  if (artistaId && categoria !== "artistas") {
    params.set("artista_id", artistaId);
  }

  return consultar(`/busca?${params}`, paginaValida);
}

export function artista(id: string) {
  return consultar(`/artistas/${encodeURIComponent(id)}`, itemValido);
}

export function discografia(id: string, pagina: number, tipo = "todos") {
  const parametros = new URLSearchParams({ pagina: String(pagina), tipo });
  return consultar(`/artistas/${encodeURIComponent(id)}/discografia?${parametros}`, paginaValida);
}

export function faixasAlbum(id: string) {
  return consultar(`/albuns/${encodeURIComponent(id)}/faixas`, faixasValidas);
}

export function catalogoLocal(termo: string, tipo: string, pagina: number) {
  const params = new URLSearchParams({ termo, tipo, pagina: String(pagina) });
  return consultar(`/local?${params}`, paginaValida);
}
