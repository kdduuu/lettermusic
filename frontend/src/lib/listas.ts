// Consultas de listas no servidor Next.js. O FastAPI e a autoridade sobre privacidade.
import { requisitarBackend } from "@/lib/backend";

export type ListaMusical = {
  id: number;
  usuario_id: number;
  titulo: string;
  descricao: string | null;
  publica: boolean;
  criada_em: string;
  atualizada_em: string | null;
};

export type ItemLista = {
  id: number;
  lista_id: number;
  obra_id: number;
  posicao: number;
  id_musicbrainz: string | null;
  titulo: string | null;
  artista: string | null;
};

type Resultado<T> =
  | { ok: true; dados: T }
  | { ok: false; status: number; mensagem: string };

export type DetalheLista = {
  lista: ListaMusical;
  itens: ItemLista[];
  destaques: ItemLista[];
  dono: boolean;
  pagina: number;
  temProxima: boolean;
};

export function idPositivo(valor: unknown): number | null {
  if (typeof valor !== "string" || !/^[1-9]\d{0,14}$/.test(valor)) return null;
  const id = Number(valor);
  return Number.isSafeInteger(id) && id > 0 ? id : null;
}

function objeto(valor: unknown): valor is Record<string, unknown> {
  return typeof valor === "object" && valor !== null && !Array.isArray(valor);
}

function listaValida(valor: unknown): valor is ListaMusical {
  return objeto(valor) &&
    typeof valor.id === "number" && Number.isSafeInteger(valor.id) &&
    typeof valor.usuario_id === "number" &&
    typeof valor.titulo === "string" &&
    (valor.descricao === null || typeof valor.descricao === "string") &&
    typeof valor.publica === "boolean" &&
    typeof valor.criada_em === "string" &&
    (valor.atualizada_em === null || typeof valor.atualizada_em === "string");
}

function itemValido(valor: unknown): valor is ItemLista {
  return objeto(valor) &&
    typeof valor.id === "number" &&
    typeof valor.lista_id === "number" &&
    typeof valor.obra_id === "number" &&
    typeof valor.posicao === "number" &&
    (valor.id_musicbrainz === null || typeof valor.id_musicbrainz === "string") &&
    (valor.titulo === null || typeof valor.titulo === "string") &&
    (valor.artista === null || typeof valor.artista === "string");
}

function erro(status: number): string {
  if (status === 401) return "Sua sessão expirou. Entre novamente.";
  if (status === 404) return "Lista não encontrada ou indisponível.";
  return "Não foi possível consultar as listas agora.";
}

async function consulta<T>(
  caminho: string,
  validar: (valor: unknown) => valor is T,
  token?: string | null,
): Promise<Resultado<T>> {
  try {
    const resposta = await requisitarBackend(caminho, {
      headers: token ? { Authorization: `Bearer ${token}` } : undefined,
    });
    if (!resposta.ok) {
      return { ok: false, status: resposta.status, mensagem: erro(resposta.status) };
    }
    const dados: unknown = await resposta.json();
    if (!validar(dados)) {
      return { ok: false, status: 502, mensagem: "A API retornou dados inesperados." };
    }
    return { ok: true, dados };
  } catch {
    return { ok: false, status: 503, mensagem: "API indisponível. Confira o FastAPI." };
  }
}

const listaDeListas = (valor: unknown): valor is ListaMusical[] =>
  Array.isArray(valor) && valor.every(listaValida);
const listaDeItens = (valor: unknown): valor is ItemLista[] =>
  Array.isArray(valor) && valor.every(itemValido);

export async function minhasListas(
  token: string,
  pagina = 1,
  porPagina = 20,
): Promise<Resultado<{ listas: ListaMusical[]; temProxima: boolean }>> {
  const resultado = await consulta(
    `/listas/minhas?pagina=${pagina}&por_pagina=${porPagina}`,
    listaDeListas,
    token,
  );
  if (!resultado.ok) return resultado;
  return { ok: true, dados: { listas: resultado.dados, temProxima: resultado.dados.length === porPagina } };
}

// Usada no formulario da pagina do album: ate 100 listas por vez, sem adivinhar IDs.
export async function listasParaAdicionar(token: string): Promise<Resultado<ListaMusical[]>> {
  return consulta("/listas/minhas?pagina=1&por_pagina=100", listaDeListas, token);
}

export async function detalheLista(
  listaId: number,
  token: string | null,
  pagina = 1,
): Promise<Resultado<DetalheLista>> {
  let dono = false;
  let lista: ListaMusical;

  if (token) {
    const propria = await consulta(`/listas/minhas/${listaId}`, listaValida, token);
    if (propria.ok) {
      lista = propria.dados;
      dono = true;
    } else if (propria.status === 401 || propria.status === 404) {
      const publica = await consulta(`/listas/${listaId}`, listaValida);
      if (!publica.ok) return publica;
      lista = publica.dados;
    } else {
      return propria;
    }
  } else {
    const publica = await consulta(`/listas/${listaId}`, listaValida);
    if (!publica.ok) return publica;
    lista = publica.dados;
  }

  const porPagina = 50;
  const prefixo = dono ? `/listas/minhas/${listaId}/itens` : `/listas/${listaId}/itens`;
  const itens = await consulta(
    `${prefixo}?pagina=${pagina}&por_pagina=${porPagina}`,
    listaDeItens,
    dono ? token : null,
  );
  if (!itens.ok) return itens;
  // A colagem sempre representa o inicio da lista, mesmo ao paginar.
  const destaques = pagina === 1
    ? { ok: true as const, dados: itens.dados.slice(0, 4) }
    : await consulta(
      `${prefixo}?pagina=1&por_pagina=4`,
      listaDeItens,
      dono ? token : null,
    );
  if (!destaques.ok) return destaques;
  return {
    ok: true,
    dados: {
      lista,
      itens: itens.dados,
      destaques: destaques.dados,
      dono,
      pagina,
      temProxima: itens.dados.length === porPagina,
    },
  };
}

export async function verificarMinhaLista(listaId: number, token: string): Promise<Resultado<ListaMusical>> {
  return consulta(`/listas/minhas/${listaId}`, listaValida, token);
}