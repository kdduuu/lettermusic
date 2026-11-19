// Contrato de leitura pública no servidor Next.js.
import { requisitarBackend } from "@/lib/backend";
import { MBID_VALIDO } from "@/lib/estado-album";

type Autor = { username: string; nome_exibicao: string };
type Obra = { id_musicbrainz: string; titulo: string; artista: string | null };
type AtividadeBase = Autor & { id: number; criada_em: string };
export type Atividade = AtividadeBase & (
  | (Obra & { tipo: "review"; texto: string })
  | (Obra & { tipo: "avaliacao"; nota: number })
  | { tipo: "lista"; titulo: string }
);
export type MembroAtivo = Autor & { contribuicoes: number };
export type ObraEmAlta = Obra & { contribuicoes: number; membros: number };
export type Comunidade = {
  janela_dias: number;
  atividades: Atividade[];
  membros_ativos: MembroAtivo[];
  em_alta: ObraEmAlta[];
};
type Resultado = { ok: true; dados: Comunidade } | { ok: false; mensagem: string };

function objeto(v: unknown): v is Record<string, unknown> {
  return typeof v === "object" && v !== null && !Array.isArray(v);
}
function inteiro(v: unknown): v is number {
  return typeof v === "number" && Number.isSafeInteger(v) && v >= 1;
}
function autor(v: unknown): v is Autor & Record<string, unknown> {
  return objeto(v) && typeof v.username === "string" && /^[a-zA-Z0-9_]{3,30}$/.test(v.username) &&
    typeof v.nome_exibicao === "string";
}
function obra(v: unknown): v is Obra & Record<string, unknown> {
  return objeto(v) && typeof v.id_musicbrainz === "string" && MBID_VALIDO.test(v.id_musicbrainz) &&
    typeof v.titulo === "string" && !!v.titulo.trim() && (v.artista === null || typeof v.artista === "string");
}
function atividade(v: unknown): v is Atividade {
  if (!autor(v) || !inteiro(v.id) || typeof v.criada_em !== "string" || !Number.isFinite(Date.parse(v.criada_em))) return false;
  if (v.tipo === "lista") return typeof v.titulo === "string" && !!v.titulo.trim();
  if (!obra(v)) return false;
  if (v.tipo === "review") return typeof v.texto === "string";
  return v.tipo === "avaliacao" && typeof v.nota === "number" && v.nota >= 0.5 && v.nota <= 5 && Number.isInteger(v.nota * 2);
}
function membro(v: unknown): v is MembroAtivo {
  return autor(v) && inteiro(v.contribuicoes);
}
function emAlta(v: unknown): v is ObraEmAlta {
  return obra(v) && inteiro(v.contribuicoes) && inteiro(v.membros) && v.membros <= v.contribuicoes;
}
function comunidadeValida(v: unknown): v is Comunidade {
  return objeto(v) && inteiro(v.janela_dias) &&
    Array.isArray(v.atividades) && v.atividades.every(atividade) &&
    Array.isArray(v.membros_ativos) && v.membros_ativos.every(membro) &&
    Array.isArray(v.em_alta) && v.em_alta.every(emAlta);
}

export async function consultarComunidade(): Promise<Resultado> {
  try {
    const resposta = await requisitarBackend("/social/comunidade");
    if (!resposta.ok) return { ok: false, mensagem: "Não foi possível carregar a comunidade agora." };
    const dados: unknown = await resposta.json();
    if (!comunidadeValida(dados)) return { ok: false, mensagem: "Resposta inesperada da API da comunidade." };
    return { ok: true, dados };
  } catch {
    return { ok: false, mensagem: "Não foi possível conectar à API da comunidade." };
  }
}