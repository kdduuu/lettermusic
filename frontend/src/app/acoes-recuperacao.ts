"use server";

import { cookies } from "next/headers";
import { revalidatePath } from "next/cache";
import { requisitarBackend } from "@/lib/backend";
import { NOME_COOKIE_SESSAO } from "@/lib/sessao";
import type { EstadoAcao } from "@/lib/estado-acoes";

const TOKEN_VALIDO = /^[A-Za-z0-9_-]{43}$/;

function erroSolicitacao(status: number): string {
  if (status === 429) return "Too many requests. Wait 15 minutes.";
  if (status === 503) return "Email delivery is unavailable.";
  return "Unable to send. Try again.";
}

export async function solicitarRecuperacao(
  _estado: EstadoAcao,
  formulario: FormData,
): Promise<EstadoAcao> {
  const email = String(formulario.get("email") ?? "").trim();

  if (!email.includes("@") || email.length > 254) {
    return { sucesso: false, mensagem: "Enter a valid email address." };
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
      mensagem: "If an account exists for this email, you will receive instructions.",
    };
  } catch {
    return { sucesso: false, mensagem: "Connection failed. Try again." };
  }
}

export async function solicitarConfirmacao(
  _estado: EstadoAcao,
  formulario: FormData,
): Promise<EstadoAcao> {
  const email = String(formulario.get("email") ?? "").trim();

  if (!email.includes("@") || email.length > 254) {
    return { sucesso: false, mensagem: "Enter a valid email address." };
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
      mensagem: "If your email is unconfirmed, we will send a new link.",
    };
  } catch {
    return { sucesso: false, mensagem: "Connection failed. Try again." };
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
    return { sucesso: false, mensagem: "Invalid reset link." };
  }

  if (senha_nova.length < 12 || senha_nova.length > 128) {
    return { sucesso: false, mensagem: "Use a password of 12 to 128 characters." };
  }

  if (senha_nova !== confirmacao) {
    return { sucesso: false, mensagem: "Passwords do not match." };
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
          ? "Invalid, expired or already used link."
          : resposta.status === 422
            ? "Check your new password."
            : "Unable to reset password.",
      };
    }

    const armazenamento = await cookies();
    armazenamento.delete(NOME_COOKIE_SESSAO);
    revalidatePath("/", "layout");

    return {
      sucesso: true,
      mensagem: "Password reset. Sign in with your new password.",
    };
  } catch {
    return { sucesso: false, mensagem: "Connection failed. Try again." };
  }
}

export async function confirmarEmail(
  _estado: EstadoAcao,
  formulario: FormData,
): Promise<EstadoAcao> {
  const token = String(formulario.get("token") ?? "");

  if (!TOKEN_VALIDO.test(token)) {
    return { sucesso: false, mensagem: "Invalid confirmation link." };
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
          ? "Invalid, expired or already used link."
          : "Unable to confirm email.",
      };
    }

    revalidatePath("/", "layout");

    return {
      sucesso: true,
      mensagem: "Email confirmed.",
    };
  } catch {
    return { sucesso: false, mensagem: "Connection failed. Try again." };
  }
}
