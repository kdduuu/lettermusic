// Contratos de leitura por MBID, executados somente no servidor Next.js.
import { requisitarBackend } from "@/lib/backend";

export type ReviewResumo = {
  username: string;
  nome_exibicao: string;
  texto: string;
  criada_em: string;
};

export type ResumoAlbum = {
  obra_id: number | null;
  media_avaliacoes: number | null;
  quantidade_avaliacoes: number;
  reviews: ReviewResumo[];
};

export type EstadoAlbum = {
  obra_id: number | null;
  ouvida: boolean;
  favorito: boolean;
  quero_ouvir: boolean;
  nota: number | null;
  review: string | null;
  quantidade_escutas: number;
};

export type Resultado<T> =
  | { ok: true; dados: T }
  | { ok: false; status: number; mensagem: string };

export const MBID_VALIDO = /^[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}$/i;

function objeto(valor: unknown): valor is Record<string, unknown> {
  return typeof valor === "object" && valor !== null && !Array.isArray(valor);
}

function nuloOuNumero(valor: unknown): valor is number | null {
  return valor === null || (typeof valor === "number" && Number.isFinite(valor));
}

function nuloOuTexto(valor: unknown): valor is string | null {
  return valor === null || typeof valor === "string";
}

function converterResumo(valor: unknown): ResumoAlbum | null {
  if (!objeto(valor) || !nuloOuNumero(valor.obra_id) ||
      !nuloOuNumero(valor.media_avaliacoes) ||
      typeof valor.quantidade_avaliacoes !== "number" ||
      !Array.isArray(valor.reviews)) return null;

  const reviews: ReviewResumo[] = [];
  for (const item of valor.reviews) {
    if (!objeto(item) || typeof item.username !== "string" ||
        typeof item.nome_exibicao !== "string" ||
        typeof item.texto !== "string" ||
        typeof item.criada_em !== "string") return null;
    reviews.push({
      username: item.username,
      nome_exibicao: item.nome_exibicao,
      texto: item.texto,
      criada_em: item.criada_em,
    });
  }
  return {
    obra_id: valor.obra_id,
    media_avaliacoes: valor.media_avaliacoes,
    quantidade_avaliacoes: valor.quantidade_avaliacoes,
    reviews,
  };
}

function converterEstado(valor: unknown): EstadoAlbum | null {
  if (!objeto(valor) || !nuloOuNumero(valor.obra_id) ||
      typeof valor.ouvida !== "boolean" ||
      typeof valor.favorito !== "boolean" ||
      typeof valor.quero_ouvir !== "boolean" ||
      !nuloOuNumero(valor.nota) || !nuloOuTexto(valor.review) ||
      typeof valor.quantidade_escutas !== "number") return null;

  return {
    obra_id: valor.obra_id,
    ouvida: valor.ouvida,
    favorito: valor.favorito,
    quero_ouvir: valor.quero_ouvir,
    nota: valor.nota,
    review: valor.review,
    quantidade_escutas: valor.quantidade_escutas,
  };
}

async function consultar<T>(
  id: string,
  sufixo: string,
  converter: (dados: unknown) => T | null,
  token?: string,
): Promise<Resultado<T>> {
  if (!MBID_VALIDO.test(id)) {
    return { ok: false, status: 422, mensagem: "Invalid music ID." };
  }
  try {
    const resposta = await requisitarBackend(
      `/catalogo/musicbrainz/${id.toLowerCase()}/${sufixo}`,
      { headers: token ? { Authorization: `Bearer ${token}` } : {} },
    );
    if (!resposta.ok) {
      return {
        ok: false,
        status: resposta.status,
        mensagem: resposta.status === 401
          ? "Session expired. Sign in again."
          : "Unable to load album activity.",
      };
    }
    const dados: unknown = await resposta.json();
    const convertido = converter(dados);
    return convertido === null
      ? { ok: false, status: 502, mensagem: "Unexpected service response." }
      : { ok: true, dados: convertido };
  } catch {
    return { ok: false, status: 503, mensagem: "Service unavailable. Try again." };
  }
}

export function obterResumoAlbum(id: string): Promise<Resultado<ResumoAlbum>> {
  return consultar(id, "social", converterResumo);
}

export function obterEstadoAlbum(id: string, token: string): Promise<Resultado<EstadoAlbum>> {
  return consultar(id, "meu-estado", converterEstado, token);
}