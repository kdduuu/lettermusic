// Contratos de leitura publica, usados somente no servidor Next.js.
import { requisitarBackend } from "@/lib/backend";
import { MBID_VALIDO } from "@/lib/estado-album";

export type ObraDestaque = {
  obra_id: number;
  id_musicbrainz: string;
  titulo: string;
  artista: string | null;
  total_escutas?: number;
  media?: number;
  quantidade_avaliacoes?: number;
};

export type ReviewFeed = {
  id: number;
  username: string;
  nome_exibicao: string;
  id_musicbrainz: string;
  titulo: string;
  artista: string | null;
  texto: string;
  nota: number | null;
  criada_em: string;
  atualizada_em: string | null;
};

export type PaginaReviews = {
  pagina: number;
  por_pagina: number;
  tem_proxima: boolean;
  resultados: ReviewFeed[];
};

type Resultado<T> = { ok: true; dados: T } | { ok: false; mensagem: string };
export type TipoDestaque = "mais-ouvidas" | "melhor-avaliadas";

function objeto(v: unknown): v is Record<string, unknown> {
  return typeof v === "object" && v !== null && !Array.isArray(v);
}
function inteiro(v: unknown): v is number {
  return typeof v === "number" && Number.isSafeInteger(v) && v >= 1;
}
function textoOuNull(v: unknown): v is string | null {
  return v === null || typeof v === "string";
}
function notaValida(v: unknown): v is number {
  return typeof v === "number" && Number.isFinite(v) && v >= 0.5 && v <= 5;
}
function obraValida(v: unknown): v is Record<string, unknown> & {
  id_musicbrainz: string; titulo: string; artista: string | null;
} {
  return objeto(v) && typeof v.id_musicbrainz === "string" && MBID_VALIDO.test(v.id_musicbrainz) &&
    typeof v.titulo === "string" && v.titulo.trim().length > 0 && textoOuNull(v.artista);
}
function destaqueValido(v: unknown, tipo: TipoDestaque): v is ObraDestaque {
  return obraValida(v) && inteiro(v.obra_id) && (tipo === "mais-ouvidas"
    ? inteiro(v.total_escutas)
    : notaValida(v.media) && inteiro(v.quantidade_avaliacoes));
}
function reviewValida(v: unknown): v is ReviewFeed {
  return obraValida(v) && inteiro(v.id) && typeof v.username === "string" &&
    /^[a-zA-Z0-9_]{3,30}$/.test(v.username) && typeof v.nome_exibicao === "string" &&
    typeof v.texto === "string" && (v.nota === null || notaValida(v.nota)) &&
    typeof v.criada_em === "string" && textoOuNull(v.atualizada_em);
}

export async function consultarDestaques(tipo: TipoDestaque): Promise<Resultado<ObraDestaque[]>> {
  try {
    const resposta = await requisitarBackend(`/descoberta/${tipo}?limite=4`);
    if (!resposta.ok) return { ok: false, mensagem: "Não foi possível carregar os destaques." };
    const dados: unknown = await resposta.json();
    if (!Array.isArray(dados) || !dados.every((v: unknown) => destaqueValido(v, tipo))) {
      return { ok: false, mensagem: "Resposta inesperada da API de descoberta." };
    }
    return { ok: true, dados };
  } catch {
    return { ok: false, mensagem: "Não foi possível conectar à API de descoberta." };
  }
}

export async function consultarFeedReviews(pagina = 1, porPagina = 12): Promise<Resultado<PaginaReviews>> {
  try {
    const resposta = await requisitarBackend(`/social/reviews?pagina=${pagina}&por_pagina=${porPagina}`);
    if (!resposta.ok) return { ok: false, mensagem: "Não foi possível carregar as reviews." };
    const dados: unknown = await resposta.json();
    if (!objeto(dados) || dados.pagina !== pagina || dados.por_pagina !== porPagina ||
        typeof dados.tem_proxima !== "boolean" || !Array.isArray(dados.resultados) ||
        !dados.resultados.every(reviewValida)) {
      return { ok: false, mensagem: "Resposta inesperada da API de reviews." };
    }
    return { ok: true, dados: { pagina, por_pagina: porPagina, tem_proxima: dados.tem_proxima, resultados: dados.resultados } };
  } catch {
    return { ok: false, mensagem: "Não foi possível conectar à API de reviews." };
  }
}