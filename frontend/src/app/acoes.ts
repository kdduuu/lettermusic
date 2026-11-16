"use server";

import { cookies } from "next/headers";
import { revalidatePath } from "next/cache";
import { redirect } from "next/navigation";
import { requisitarBackend } from "@/lib/backend";
import { NOME_COOKIE_SESSAO, obterTokenSessao } from "@/lib/sessao";
import type { EstadoAcao } from "@/lib/estado-acoes";

async function autenticar(identificador: string, senha: string): Promise<EstadoAcao> {
  try {
    const resposta = await requisitarBackend("/auth/login", {
      method: "POST",
      body: JSON.stringify({ identificador, senha }),
    });

    if (!resposta.ok) {
      return {
        sucesso: false,
        mensagem: resposta.status === 401
          ? "Usuário/e-mail ou senha incorretos."
          : "Não foi possível entrar agora. Tente novamente.",
      };
    }

    const dados: unknown = await resposta.json();
    if (
      !dados || typeof dados !== "object" ||
      !("access_token" in dados) || typeof dados.access_token !== "string" ||
      !dados.access_token
    ) {
      return { sucesso: false, mensagem: "Resposta inesperada da autenticação." };
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
    return { sucesso: false, mensagem: "API indisponível. Confira se o FastAPI está ligado." };
  }
}

export async function entrar(
  _estado: EstadoAcao,
  formulario: FormData,
): Promise<EstadoAcao> {
  const identificador = String(formulario.get("identificador") ?? "").trim();
  const senha = String(formulario.get("senha") ?? "");
  if (!identificador || !senha) {
    return { sucesso: false, mensagem: "Preencha seu usuário/e-mail e sua senha." };
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
    return { sucesso: false, mensagem: "Confira os campos e use uma senha de 12 a 128 caracteres." };
  }

  try {
    const resposta = await requisitarBackend("/usuarios", {
      method: "POST",
      body: JSON.stringify({ username, nome_exibicao, email, senha }),
    });
    if (!resposta.ok) {
      return {
        sucesso: false,
        mensagem: resposta.status === 409
          ? "Nome de usuário ou e-mail indisponível."
          : resposta.status === 422
            ? "Dados inválidos. Verifique os campos informados."
            : "Não foi possível criar a conta agora.",
      };
    }
  } catch {
    return { sucesso: false, mensagem: "API indisponível. Confira se o FastAPI está ligado." };
  }

  const login = await autenticar(username, senha);
  if (!login.sucesso) {
    return { sucesso: false, mensagem: "Conta criada! Entre pela página de login." };
  }

  revalidatePath("/", "layout");
  redirect("/");
}

export async function sair(): Promise<void> {
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

export async function registrarInteracao(
  _estado: EstadoAcao,
  formulario: FormData,
): Promise<EstadoAcao> {
  const id = String(formulario.get("id_musicbrainz") ?? "");
  const tipo = String(formulario.get("tipo") ?? "");

  const mbidValido = /^[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}$/i;
  if (!mbidValido.test(id) || !Object.prototype.hasOwnProperty.call(ENDPOINTS, tipo)) {
    return { sucesso: false, mensagem: "Dados da interação inválidos." };
  }

  const token = await obterTokenSessao();
  if (!token) return { sucesso: false, mensagem: "Entre na sua conta para registrar este álbum." };

  try {
    const resposta = await requisitarBackend(ENDPOINTS[tipo as TipoInteracao], {
      method: "POST",
      headers: { Authorization: `Bearer ${token}` },
      body: JSON.stringify({ obra: { id_musicbrainz: id.toLowerCase() } }),
    });

    if (resposta.status === 401) {
      return { sucesso: false, mensagem: "Sua sessão expirou. Entre novamente." };
    }
    if (resposta.status === 409) {
      return { sucesso: true, mensagem: "Este álbum já está registrado nessa categoria." };
    }
    if (!resposta.ok) {
      return {
        sucesso: false,
        mensagem: resposta.status === 502
          ? "MusicBrainz indisponível. Tente novamente."
          : "Não foi possível salvar sua interação.",
      };
    }

    revalidatePath("/biblioteca");
    return { sucesso: true, mensagem: "Salvo na sua biblioteca!" };
  } catch {
    return { sucesso: false, mensagem: "Falha de conexão. Tente novamente." };
  }
}