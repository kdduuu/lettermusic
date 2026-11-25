import { requisitarBackend } from "@/lib/backend";

export type ListaDescoberta = {
  id: number;
  titulo: string;
  descricao: string | null;
  username: string;
  nome_exibicao: string;
  total_itens: number;
  criada_em: string;
};

export type PaginaListas = {
  pagina: number;
  por_pagina: number;
  total: number;
  tem_proxima: boolean;
  resultados: ListaDescoberta[];
};

type Resultado =
  | { ok: true; dados: PaginaListas }
  | { ok: false; mensagem: string };

function objeto(valor: unknown): valor is Record<string, unknown> {
  return typeof valor === "object" &&
    valor !== null && !Array.isArray(valor);
}

function listaValida(valor: unknown): valor is ListaDescoberta {
  return objeto(valor) &&
    typeof valor.id === "number" &&
    Number.isSafeInteger(valor.id) &&
    typeof valor.titulo === "string" &&
    (valor.descricao === null || typeof valor.descricao === "string") &&
    typeof valor.username === "string" &&
    typeof valor.nome_exibicao === "string" &&
    typeof valor.total_itens === "number" &&
    typeof valor.criada_em === "string";
}

function paginaValida(valor: unknown): valor is PaginaListas {
  return objeto(valor) &&
    typeof valor.pagina === "number" &&
    typeof valor.por_pagina === "number" &&
    typeof valor.total === "number" &&
    typeof valor.tem_proxima === "boolean" &&
    Array.isArray(valor.resultados) &&
    valor.resultados.every(listaValida);
}

export async function obterListasPublicas(
  pagina: number,
): Promise<Resultado> {
  try {
    const resposta = await requisitarBackend(
      `/listas/publicas?pagina=${pagina}&por_pagina=12`
    );

    if (!resposta.ok) {
      return {
        ok: false,
        mensagem: "Unable to load public lists.",
      };
    }

    const dados: unknown = await resposta.json();

    if (!paginaValida(dados)) {
      return {
        ok: false,
        mensagem: "Unexpected service response.",
      };
    }

    return { ok: true, dados };
  } catch {
    return {
      ok: false,
      mensagem: "Lists temporarily unavailable.",
    };
  }
}
