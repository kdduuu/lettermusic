"use server";

import { cookies } from "next/headers";
import { revalidatePath } from "next/cache";
import { redirect } from "next/navigation";
import { requisitarBackend } from "@/lib/backend";
import { NOME_COOKIE_SESSAO, obterTokenSessao } from "@/lib/sessao";
import type { EstadoAcao } from "@/lib/estado-acoes";
import { MBID_VALIDO, obterEstadoAlbum } from "@/lib/estado-album";

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

type ContextoAlbum =
  | { ok: true; id: string; token: string; obraId: number | null;
      nota: number | null; review: string | null }
  | { ok: false; mensagem: string };

async function contextoAlbum(formulario: FormData): Promise<ContextoAlbum> {
  const id = String(formulario.get("id_musicbrainz") ?? "").toLowerCase();
  if (!MBID_VALIDO.test(id)) return { ok: false, mensagem: "ID musical inválido." };

  const token = await obterTokenSessao();
  if (!token) return { ok: false, mensagem: "Entre na sua conta para continuar." };

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
  if (status === 401) return "Sua sessão expirou. Entre novamente.";
  if (status === 404) return "Registro não encontrado. Atualize a página.";
  if (status === 409) return "O registro já existe. Atualize a página.";
  if (status === 422) return "Os dados enviados foram recusados pela API.";
  if (status === 502) return "MusicBrainz indisponível. Tente novamente.";
  return "Não foi possível concluir sua ação.";
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
    return { sucesso: false, mensagem: "Ação inválida." };
  }

  const contexto = await contextoAlbum(formulario);
  if (!contexto.ok) return { sucesso: false, mensagem: contexto.mensagem };
  const caminho = ENDPOINTS[tipo as TipoInteracao];

  if (operacao === "remover" && contexto.obraId === null) {
    return { sucesso: false, mensagem: "Este álbum ainda não está na sua biblioteca." };
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

    // DELETE é 204; "Já ouvi" repetido é idempotente. O estado é revalidado no servidor.
    if (resposta.status === 409 && operacao === "adicionar") {
      atualizarAlbum(contexto.id);
      return { sucesso: true, mensagem: "Este álbum já estava registrado." };
    }
    if (!resposta.ok) return { sucesso: false, mensagem: mensagemFalha(resposta.status) };
    atualizarAlbum(contexto.id);
    return {
      sucesso: true,
      mensagem: operacao === "remover" ? "Removido da biblioteca." : "Salvo na biblioteca!",
    };
  } catch {
    return { sucesso: false, mensagem: "Falha de conexão. Tente novamente." };
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
    return { sucesso: true, mensagem: "Escuta registrada no histórico!" };
  } catch {
    return { sucesso: false, mensagem: "Falha de conexão. Tente novamente." };
  }
}

export async function salvarAvaliacao(
  _estado: EstadoAcao,
  formulario: FormData,
): Promise<EstadoAcao> {
  const nota = Number(formulario.get("nota"));
  if (!Number.isFinite(nota) || nota < 0.5 || nota > 5 || nota * 2 % 1 !== 0) {
    return { sucesso: false, mensagem: "Escolha uma nota entre 0,5 e 5 estrelas." };
  }
  const contexto = await contextoAlbum(formulario);
  if (!contexto.ok) return { sucesso: false, mensagem: contexto.mensagem };

  const edicao = contexto.nota !== null;
  if (edicao && contexto.obraId === null) {
    return { sucesso: false, mensagem: "Avaliação sem álbum correspondente." };
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
      mensagem: edicao ? "Avaliação atualizada!" : "Avaliação registrada! Uma escuta foi adicionada.",
    };
  } catch {
    return { sucesso: false, mensagem: "Falha de conexão. Tente novamente." };
  }
}

export async function salvarReview(
  _estado: EstadoAcao,
  formulario: FormData,
): Promise<EstadoAcao> {
  const texto = String(formulario.get("texto") ?? "").trim();
  if (!texto || texto.length > 5000) {
    return { sucesso: false, mensagem: "Escreva uma review de até 5.000 caracteres." };
  }
  const contexto = await contextoAlbum(formulario);
  if (!contexto.ok) return { sucesso: false, mensagem: contexto.mensagem };

  const edicao = contexto.review !== null;
  if (edicao && contexto.obraId === null) {
    return { sucesso: false, mensagem: "Review sem álbum correspondente." };
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
      mensagem: edicao ? "Review atualizada!" : "Review publicada! Uma escuta foi adicionada.",
    };
  } catch {
    return { sucesso: false, mensagem: "Falha de conexão. Tente novamente." };
  }
}