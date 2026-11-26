"use server";

import { cookies } from "next/headers";
import { revalidatePath } from "next/cache";
import { redirect } from "next/navigation";
import { requisitarBackend } from "@/lib/backend";
import { NOME_COOKIE_SESSAO, obterTokenSessao } from "@/lib/sessao";
import type { EstadoAcao } from "@/lib/estado-acoes";
import { MBID_VALIDO, obterEstadoAlbum } from "@/lib/estado-album";

async function autenticar(identificador: string, senha: string): Promise<EstadoAcao & { verificacaoPendente?: boolean }> {
  try {
    const resposta = await requisitarBackend("/auth/login", {
      method: "POST",
      body: JSON.stringify({ identificador, senha }),
    });

    if (!resposta.ok) {
      return {
        sucesso: false,
        verificacaoPendente: resposta.status === 403,
        mensagem: resposta.status === 429
          ? "Too many attempts. Wait one minute."
          : resposta.status === 401
            ? "Incorrect username/email or password."
            : resposta.status === 403
              ? "Confirm your email before signing in. Request another link if needed."
              : "Unable to sign in. Try again.",
      };
    }

    const dados: unknown = await resposta.json();
    if (
      !dados || typeof dados !== "object" ||
      !("access_token" in dados) || typeof dados.access_token !== "string" ||
      !dados.access_token
    ) {
      return { sucesso: false, mensagem: "Unexpected authentication response." };
    }

    const armazenamento = await cookies();
    armazenamento.set(NOME_COOKIE_SESSAO, dados.access_token, {
      httpOnly: true,
      secure: process.env.NODE_ENV === "production",
      sameSite: "lax",
      path: "/",
      maxAge: 30 * 60, // O JWT emitido pelo FastAPI também vence em 30 minutos.
    });
    return { sucesso: true, mensagem: "" };
  } catch {
    return { sucesso: false, mensagem: "Service unavailable. Try again later." };
  }
}

export async function entrar(
  _estado: EstadoAcao,
  formulario: FormData,
): Promise<EstadoAcao> {
  const identificador = String(formulario.get("identificador") ?? "").trim();
  const senha = String(formulario.get("senha") ?? "");
  if (!identificador || !senha) {
    return { sucesso: false, mensagem: "Enter your username/email and password." };
  }

  const resultado = await autenticar(identificador, senha);
  if (!resultado.sucesso) return resultado;

  revalidatePath("/", "layout");
  redirect("/");
}

export async function cadastrar(
  _estado: EstadoAcao,
  formulario: FormData,
): Promise<EstadoAcao> {
  const username = String(formulario.get("username") ?? "").trim();
  const nome_exibicao = String(formulario.get("nome_exibicao") ?? "").trim();
  const email = String(formulario.get("email") ?? "").trim();
  const senha = String(formulario.get("senha") ?? "");

  if (!/^[a-zA-Z0-9_]{3,30}$/.test(username) ||
      nome_exibicao.length < 2 || nome_exibicao.length > 80 ||
      email.length > 254 || !email.includes("@") ||
      senha.length < 12 || senha.length > 128) {
    return { sucesso: false, mensagem: "Check the fields and use a password of 12 to 128 characters." };
  }

  try {
    const resposta = await requisitarBackend("/usuarios", {
      method: "POST",
      body: JSON.stringify({ username, nome_exibicao, email, senha }),
    });
    if (!resposta.ok) {
      return {
        sucesso: false,
        mensagem: resposta.status === 503
          ? "Sign-up temporarily unavailable. Try again later."
          : resposta.status === 429
            ? "Too many sign-up attempts. Try again in 15 minutes."
            : resposta.status === 409
          ? "Username or email unavailable."
          : resposta.status === 422
            ? "Invalid details. Check the fields."
            : "Unable to create account.",
      };
    }
  } catch {
    return { sucesso: false, mensagem: "Service unavailable. Try again later." };
  }

  const login = await autenticar(username, senha);
  if (!login.sucesso) {
    return { sucesso: true, mensagem: login.verificacaoPendente
      ? "Account created. Check your email to confirm your address before signing in."
      : "Account created. Sign in to continue." };
  }

  revalidatePath("/", "layout");
  redirect("/");
}

export async function sair(): Promise<void> {
  const token = await obterTokenSessao();

  if (token) {
    try {
      await requisitarBackend("/auth/sessoes/revogar", {
        method: "POST",
        headers: { Authorization: `Bearer ${token}` },
      });
    } catch {
      // Mesmo sem API, limpar o cookie deste navegador.
    }
  }

  const armazenamento = await cookies();
  armazenamento.delete(NOME_COOKIE_SESSAO);
  revalidatePath("/", "layout");
  redirect("/");
}

type TipoInteracao = "ouvida" | "favorito" | "quero-ouvir";
const ENDPOINTS: Record<TipoInteracao, string> = {
  ouvida: "/interacoes/obras-ouvidas",
  favorito: "/biblioteca/favoritos",
  "quero-ouvir": "/biblioteca/quero-ouvir",
};

type ContextoAlbum =
  | { ok: true; id: string; token: string; obraId: number | null;
      nota: number | null; review: string | null }
  | { ok: false; mensagem: string };

async function contextoAlbum(formulario: FormData): Promise<ContextoAlbum> {
  const id = String(formulario.get("id_musicbrainz") ?? "").toLowerCase();
  if (!MBID_VALIDO.test(id)) return { ok: false, mensagem: "Invalid music ID." };

  const token = await obterTokenSessao();
  if (!token) return { ok: false, mensagem: "Sign in to continue." };

  // O ID interno vem da nossa API autenticada, nunca de um campo oculto confiado ao cliente.
  const consulta = await obterEstadoAlbum(id, token);
  if (!consulta.ok) return { ok: false, mensagem: consulta.mensagem };
  return {
    ok: true, id, token,
    obraId: consulta.dados.obra_id,
    nota: consulta.dados.nota,
    review: consulta.dados.review,
  };
}

function atualizarAlbum(id: string): void {
  revalidatePath(`/albuns/${id}`);
  revalidatePath("/biblioteca");
}

function mensagemFalha(status: number): string {
  if (status === 401) return "Session expired. Sign in again.";
  if (status === 404) return "Record not found. Refresh the page.";
  if (status === 409) return "Record already exists. Refresh the page.";
  if (status === 422) return "Invalid request.";
  if (status === 502) return "MusicBrainz unavailable. Try again.";
  return "Unable to complete your action.";
}

export async function registrarInteracao(
  _estado: EstadoAcao,
  formulario: FormData,
): Promise<EstadoAcao> {
  const tipo = String(formulario.get("tipo") ?? "");
  const operacao = String(formulario.get("operacao") ?? "adicionar");
  if (!Object.prototype.hasOwnProperty.call(ENDPOINTS, tipo) ||
      (operacao !== "adicionar" && operacao !== "remover") ||
      (tipo === "ouvida" && operacao === "remover")) {
    return { sucesso: false, mensagem: "Invalid action." };
  }

  const contexto = await contextoAlbum(formulario);
  if (!contexto.ok) return { sucesso: false, mensagem: contexto.mensagem };
  const caminho = ENDPOINTS[tipo as TipoInteracao];

  if (operacao === "remover" && contexto.obraId === null) {
    return { sucesso: false, mensagem: "This album is not in your library yet." };
  }

  try {
    const resposta = await requisitarBackend(
      operacao === "remover" ? `${caminho}/${contexto.obraId}` : caminho,
      {
        method: operacao === "remover" ? "DELETE" : "POST",
        headers: { Authorization: `Bearer ${contexto.token}` },
        ...(operacao === "adicionar"
          ? { body: JSON.stringify({ obra: { id_musicbrainz: contexto.id } }) }
          : {}),
      },
    );

    // DELETE é 204; "Listened" repetido é idempotente. O estado é revalidado no servidor.
    if (resposta.status === 409 && operacao === "adicionar") {
      atualizarAlbum(contexto.id);
      return { sucesso: true, mensagem: "This album was already logged." };
    }
    if (!resposta.ok) return { sucesso: false, mensagem: mensagemFalha(resposta.status) };
    atualizarAlbum(contexto.id);
    return {
      sucesso: true,
      mensagem: operacao === "remover" ? "Removed from library." : "Saved to library.",
    };
  } catch {
    return { sucesso: false, mensagem: "Connection failed. Try again." };
  }
}

export async function registrarEscuta(
  _estado: EstadoAcao,
  formulario: FormData,
): Promise<EstadoAcao> {
  const contexto = await contextoAlbum(formulario);
  if (!contexto.ok) return { sucesso: false, mensagem: contexto.mensagem };

  try {
    const resposta = await requisitarBackend("/interacoes/escutas", {
      method: "POST",
      headers: { Authorization: `Bearer ${contexto.token}` },
      body: JSON.stringify({ obra: { id_musicbrainz: contexto.id } }),
    });
    if (!resposta.ok) return { sucesso: false, mensagem: mensagemFalha(resposta.status) };
    atualizarAlbum(contexto.id);
    return { sucesso: true, mensagem: "Play logged." };
  } catch {
    return { sucesso: false, mensagem: "Connection failed. Try again." };
  }
}

export async function salvarAvaliacao(
  _estado: EstadoAcao,
  formulario: FormData,
): Promise<EstadoAcao> {
  const nota = Number(formulario.get("nota"));
  if (!Number.isFinite(nota) || nota < 0.5 || nota > 5 || nota * 2 % 1 !== 0) {
    return { sucesso: false, mensagem: "Choose a rating from 0.5 to 5 stars." };
  }
  const contexto = await contextoAlbum(formulario);
  if (!contexto.ok) return { sucesso: false, mensagem: contexto.mensagem };

  const edicao = contexto.nota !== null;
  if (edicao && contexto.obraId === null) {
    return { sucesso: false, mensagem: "Album not found for rating." };
  }

  try {
    const resposta = await requisitarBackend(
      edicao ? `/interacoes/avaliacoes/${contexto.obraId}` : "/interacoes/avaliacoes",
      {
        method: edicao ? "PATCH" : "POST",
        headers: { Authorization: `Bearer ${contexto.token}` },
        body: JSON.stringify(edicao
          ? { nota }
          : { obra: { id_musicbrainz: contexto.id }, nota }),
      },
    );
    if (!resposta.ok) return { sucesso: false, mensagem: mensagemFalha(resposta.status) };
    atualizarAlbum(contexto.id);
    return {
      sucesso: true,
      mensagem: edicao ? "Rating updated." : "Rating saved and play logged.",
    };
  } catch {
    return { sucesso: false, mensagem: "Connection failed. Try again." };
  }
}

export async function salvarReview(
  _estado: EstadoAcao,
  formulario: FormData,
): Promise<EstadoAcao> {
  const texto = String(formulario.get("texto") ?? "").trim();
  if (!texto || texto.length > 5000) {
    return { sucesso: false, mensagem: "Write a review of up to 5,000 characters." };
  }
  const contexto = await contextoAlbum(formulario);
  if (!contexto.ok) return { sucesso: false, mensagem: contexto.mensagem };

  const edicao = contexto.review !== null;
  if (edicao && contexto.obraId === null) {
    return { sucesso: false, mensagem: "Album not found for review." };
  }

  try {
    const resposta = await requisitarBackend(
      edicao ? `/interacoes/reviews/${contexto.obraId}` : "/interacoes/reviews",
      {
        method: edicao ? "PATCH" : "POST",
        headers: { Authorization: `Bearer ${contexto.token}` },
        body: JSON.stringify(edicao
          ? { texto }
          : { obra: { id_musicbrainz: contexto.id }, texto }),
      },
    );
    if (!resposta.ok) return { sucesso: false, mensagem: mensagemFalha(resposta.status) };
    atualizarAlbum(contexto.id);
    return {
      sucesso: true,
      mensagem: edicao ? "Review updated." : "Review published and play logged.",
    };
  } catch {
    return { sucesso: false, mensagem: "Connection failed. Try again." };
  }
}

export async function removerReview(
  _estado: EstadoAcao,
  formulario: FormData,
): Promise<EstadoAcao> {
  const contexto = await contextoAlbum(formulario);

  if (!contexto.ok) {
    return { sucesso: false, mensagem: contexto.mensagem };
  }

  if (contexto.obraId === null || contexto.review === null) {
    return {
      sucesso: false,
      mensagem: "You have no review for this album.",
    };
  }

  try {
    const resposta = await requisitarBackend(
      `/interacoes/reviews/${contexto.obraId}`,
      {
        method: "DELETE",
        headers: {
          Authorization: `Bearer ${contexto.token}`,
        },
      },
    );

    if (!resposta.ok) {
      return {
        sucesso: false,
        mensagem: mensagemFalha(resposta.status),
      };
    }

    atualizarAlbum(contexto.id);
    revalidatePath("/reviews");
    revalidatePath("/biblioteca");

    return {
      sucesso: true,
      mensagem: "Review deleted.",
    };
  } catch {
    return {
      sucesso: false,
      mensagem: "Connection failed. Try again.",
    };
  }
}
