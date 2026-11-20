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
    return { sucesso: false, mensagem: "Informe um nome de 2 a 80 caracteres." };
  }

  const token = await obterTokenSessao();
  if (!token) return { sucesso: false, mensagem: "Entre novamente na sua conta." };

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
          ? "Sua sessão expirou."
          : "Não foi possível atualizar seu nome.",
      };
    }

    revalidatePath("/", "layout");
    return { sucesso: true, mensagem: "Nome atualizado com sucesso!" };
  } catch {
    return { sucesso: false, mensagem: "Falha de conexão. Tente novamente." };
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
    return { sucesso: false, mensagem: "A nova senha deve ter de 12 a 128 caracteres." };
  }

  if (senha_nova !== confirmacao) {
    return { sucesso: false, mensagem: "As novas senhas não coincidem." };
  }

  if (senha_atual === senha_nova) {
    return { sucesso: false, mensagem: "Escolha uma senha diferente da atual." };
  }

  const token = await obterTokenSessao();
  if (!token) return { sucesso: false, mensagem: "Entre novamente na sua conta." };

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
        mensagem: resposta.status === 400
          ? "Senha atual incorreta."
          : resposta.status === 401
            ? "Sua sessão expirou."
            : "Não foi possível alterar a senha.",
      };
    }

    sucesso = true;
  } catch {
    return { sucesso: false, mensagem: "Falha de conexão. Tente novamente." };
  }

  if (sucesso) {
    const armazenamento = await cookies();
    armazenamento.delete(NOME_COOKIE_SESSAO);
    revalidatePath("/", "layout");
    redirect("/entrar");
  }

  return { sucesso: false, mensagem: "Não foi possível alterar a senha." };
}
