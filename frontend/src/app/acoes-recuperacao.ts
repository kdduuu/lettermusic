"use server";

import { cookies } from "next/headers";
import { revalidatePath } from "next/cache";
import { requisitarBackend } from "@/lib/backend";
import { NOME_COOKIE_SESSAO } from "@/lib/sessao";
import type { EstadoAcao } from "@/lib/estado-acoes";

const TOKEN_VALIDO = /^[A-Za-z0-9_-]{43}$/;

function erroSolicitacao(status: number): string {
  if (status === 429) return "Muitas solicitações. Aguarde 15 minutos.";
  if (status === 503) return "O envio de e-mails ainda não está disponível.";
  return "Não foi possível enviar agora. Tente novamente.";
}

export async function solicitarRecuperacao(
  _estado: EstadoAcao,
  formulario: FormData,
): Promise<EstadoAcao> {
  const email = String(formulario.get("email") ?? "").trim();

  if (!email.includes("@") || email.length > 254) {
    return { sucesso: false, mensagem: "Informe um e-mail válido." };
  }

  try {
    const resposta = await requisitarBackend("/auth/senha/solicitar", {
      method: "POST",
      body: JSON.stringify({ email }),
    });

    if (!resposta.ok) {
      return { sucesso: false, mensagem: erroSolicitacao(resposta.status) };
    }

    return {
      sucesso: true,
      mensagem: "Se existir uma conta com esse e-mail, você receberá as instruções.",
    };
  } catch {
    return { sucesso: false, mensagem: "Falha de conexão. Tente novamente." };
  }
}

export async function solicitarConfirmacao(
  _estado: EstadoAcao,
  formulario: FormData,
): Promise<EstadoAcao> {
  const email = String(formulario.get("email") ?? "").trim();

  if (!email.includes("@") || email.length > 254) {
    return { sucesso: false, mensagem: "Informe um e-mail válido." };
  }

  try {
    const resposta = await requisitarBackend("/auth/email/solicitar", {
      method: "POST",
      body: JSON.stringify({ email }),
    });

    if (!resposta.ok) {
      return { sucesso: false, mensagem: erroSolicitacao(resposta.status) };
    }

    return {
      sucesso: true,
      mensagem: "Se o e-mail estiver pendente de confirmação, enviaremos um novo link.",
    };
  } catch {
    return { sucesso: false, mensagem: "Falha de conexão. Tente novamente." };
  }
}

export async function redefinirSenha(
  _estado: EstadoAcao,
  formulario: FormData,
): Promise<EstadoAcao> {
  const token = String(formulario.get("token") ?? "");
  const senha_nova = String(formulario.get("senha_nova") ?? "");
  const confirmacao = String(formulario.get("confirmacao") ?? "");

  if (!TOKEN_VALIDO.test(token)) {
    return { sucesso: false, mensagem: "Link de recuperação inválido." };
  }

  if (senha_nova.length < 12 || senha_nova.length > 128) {
    return { sucesso: false, mensagem: "Use uma senha de 12 a 128 caracteres." };
  }

  if (senha_nova !== confirmacao) {
    return { sucesso: false, mensagem: "As senhas não coincidem." };
  }

  try {
    const resposta = await requisitarBackend("/auth/senha/redefinir", {
      method: "POST",
      body: JSON.stringify({ token, senha_nova }),
    });

    if (!resposta.ok) {
      return {
        sucesso: false,
        mensagem: resposta.status === 400
          ? "Link inválido, expirado ou já utilizado."
          : resposta.status === 422
            ? "Verifique a nova senha."
            : "Não foi possível redefinir sua senha.",
      };
    }

    const armazenamento = await cookies();
    armazenamento.delete(NOME_COOKIE_SESSAO);
    revalidatePath("/", "layout");

    return {
      sucesso: true,
      mensagem: "Senha redefinida! Entre novamente com sua nova senha.",
    };
  } catch {
    return { sucesso: false, mensagem: "Falha de conexão. Tente novamente." };
  }
}

export async function confirmarEmail(
  _estado: EstadoAcao,
  formulario: FormData,
): Promise<EstadoAcao> {
  const token = String(formulario.get("token") ?? "");

  if (!TOKEN_VALIDO.test(token)) {
    return { sucesso: false, mensagem: "Link de confirmação inválido." };
  }

  try {
    const resposta = await requisitarBackend("/auth/email/confirmar", {
      method: "POST",
      body: JSON.stringify({ token }),
    });

    if (!resposta.ok) {
      return {
        sucesso: false,
        mensagem: resposta.status === 400
          ? "Link inválido, expirado ou já utilizado."
          : "Não foi possível confirmar seu e-mail.",
      };
    }

    revalidatePath("/", "layout");

    return {
      sucesso: true,
      mensagem: "E-mail confirmado com sucesso!",
    };
  } catch {
    return { sucesso: false, mensagem: "Falha de conexão. Tente novamente." };
  }
}
