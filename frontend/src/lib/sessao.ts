import { cookies } from "next/headers";
import { requisitarBackend } from "@/lib/backend";

export const NOME_COOKIE_SESSAO = "lettermusic_sessao";

export type UsuarioAutenticado = {
  id: number;
  username: string;
  nome_exibicao: string;
};

export async function obterTokenSessao(): Promise<string | null> {
  const armazenamento = await cookies();
  return armazenamento.get(NOME_COOKIE_SESSAO)?.value ?? null;
}

export async function obterUsuarioAutenticado(): Promise<UsuarioAutenticado | null> {
  const token = await obterTokenSessao();
  if (!token) return null;

  try {
    const resposta = await requisitarBackend("/auth/me", {
      headers: { Authorization: `Bearer ${token}` },
    });
    if (!resposta.ok) return null;

    const dados: unknown = await resposta.json();
    if (
      typeof dados !== "object" || dados === null ||
      !("id" in dados) || typeof dados.id !== "number" ||
      !("username" in dados) || typeof dados.username !== "string" ||
      !("nome_exibicao" in dados) || typeof dados.nome_exibicao !== "string"
    ) return null;

    return {
      id: dados.id,
      username: dados.username,
      nome_exibicao: dados.nome_exibicao,
    };
  } catch {
    return null;
  }
}