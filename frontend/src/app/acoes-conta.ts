"use server";

import { cookies } from "next/headers";
import { revalidatePath } from "next/cache";
import { redirect } from "next/navigation";
import { requisitarBackend } from "@/lib/backend";
import { NOME_COOKIE_SESSAO, obterTokenSessao } from "@/lib/sessao";
import type { EstadoAcao } from "@/lib/estado-acoes";

export async function atualizarNome(
  _estado: EstadoAcao,
  formulario: FormData,
): Promise<EstadoAcao> {
  const nome_exibicao = String(
    formulario.get("nome_exibicao") ?? ""
  ).trim();

  if (nome_exibicao.length < 2 || nome_exibicao.length > 80) {
    return { sucesso: false, mensagem: "Enter a name of 2 to 80 characters." };
  }

  const token = await obterTokenSessao();
  if (!token) return { sucesso: false, mensagem: "Sign in again." };

  try {
    const resposta = await requisitarBackend("/auth/conta", {
      method: "PATCH",
      headers: { Authorization: `Bearer ${token}` },
      body: JSON.stringify({ nome_exibicao }),
    });

    if (!resposta.ok) {
      return {
        sucesso: false,
        mensagem: resposta.status === 401
          ? "Session expired."
          : "Unable to update your name.",
      };
    }

    revalidatePath("/", "layout");
    return { sucesso: true, mensagem: "Name updated." };
  } catch {
    return { sucesso: false, mensagem: "Connection failed. Try again." };
  }
}

export async function atualizarSenha(
  _estado: EstadoAcao,
  formulario: FormData,
): Promise<EstadoAcao> {
  const senha_atual = String(formulario.get("senha_atual") ?? "");
  const senha_nova = String(formulario.get("senha_nova") ?? "");
  const confirmacao = String(formulario.get("confirmacao") ?? "");

  if (!senha_atual || senha_nova.length < 12 || senha_nova.length > 128) {
    return { sucesso: false, mensagem: "The new password must have 12 to 128 characters." };
  }

  if (senha_nova !== confirmacao) {
    return { sucesso: false, mensagem: "The new passwords do not match." };
  }

  if (senha_atual === senha_nova) {
    return { sucesso: false, mensagem: "Choose a different password." };
  }

  const token = await obterTokenSessao();
  if (!token) return { sucesso: false, mensagem: "Sign in again." };

  let sucesso = false;

  try {
    const resposta = await requisitarBackend("/auth/senha", {
      method: "POST",
      headers: { Authorization: `Bearer ${token}` },
      body: JSON.stringify({ senha_atual, senha_nova }),
    });

    if (!resposta.ok) {
      return {
        sucesso: false,
        mensagem: resposta.status === 429
          ? "Too many attempts. Try again in a few minutes."
          : resposta.status === 400
            ? "Incorrect current password."
            : resposta.status === 401
              ? "Session expired."
              : "Unable to change password.",
      };
    }

    sucesso = true;
  } catch {
    return { sucesso: false, mensagem: "Connection failed. Try again." };
  }

  if (sucesso) {
    const armazenamento = await cookies();
    armazenamento.delete(NOME_COOKIE_SESSAO);
    revalidatePath("/", "layout");
    redirect("/entrar");
  }

  return { sucesso: false, mensagem: "Unable to change password." };
}

export async function excluirConta(
  _estado: EstadoAcao,
  formulario: FormData,
): Promise<EstadoAcao> {
  const senha_atual = String(
    formulario.get("senha_atual") ?? ""
  );

  const confirmacao = String(
    formulario.get("confirmacao_exclusao") ?? ""
  ).trim();

  if (!senha_atual || confirmacao !== "DELETE") {
    return {
      sucesso: false,
      mensagem: "Enter your password and type DELETE.",
    };
  }

  const token = await obterTokenSessao();

  if (!token) {
    return {
      sucesso: false,
      mensagem: "Sign in again to delete your account.",
    };
  }

  try {
    const resposta = await requisitarBackend("/auth/conta", {
      method: "DELETE",
      headers: { Authorization: `Bearer ${token}` },
      body: JSON.stringify({ senha_atual }),
    });

    if (!resposta.ok) {
      return {
        sucesso: false,
        mensagem: resposta.status === 429
          ? "Too many attempts. Try again in a few minutes."
          : resposta.status === 400
            ? "Incorrect current password."
            : resposta.status === 401
              ? "Session expired. Sign in again."
              : "Unable to delete account.",
      };
    }
  } catch {
    return {
      sucesso: false,
      mensagem: "Connection failed. Try again.",
    };
  }

  const armazenamento = await cookies();
  armazenamento.delete(NOME_COOKIE_SESSAO);
  revalidatePath("/", "layout");
  redirect("/");
}