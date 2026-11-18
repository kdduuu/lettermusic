"use server";

import { revalidatePath } from "next/cache";
import { redirect } from "next/navigation";
import { requisitarBackend } from "@/lib/backend";
import { MBID_VALIDO } from "@/lib/estado-album";
import { idPositivo } from "@/lib/listas";
import { obterTokenSessao } from "@/lib/sessao";
import type { EstadoAcao } from "@/lib/estado-acoes";

function erroStatus(status: number): string {
  if (status === 401) return "Sua sessão expirou. Faça login novamente.";
  if (status === 403 || status === 404) return "Lista ou item indisponível para esta conta.";
  if (status === 409) return "Este álbum já está nesta lista.";
  if (status === 422) return "Dados inválidos. Confira o formulário.";
  if (status === 502) return "O catálogo musical está temporariamente indisponível.";
  return "Não foi possível concluir a operação.";
}

async function tokenAutenticado(): Promise<string | null> {
  return obterTokenSessao();
}

function dadosLista(form: FormData):
  | { ok: true; titulo: string; descricao: string | null; publica: boolean }
  | { ok: false; mensagem: string } {
  const titulo = String(form.get("titulo") ?? "").trim();
  const descricao = String(form.get("descricao") ?? "").trim();
  const publica = form.get("publica") === "on";
  if (!titulo || titulo.length > 120 || descricao.length > 500) {
    return { ok: false, mensagem: "Título obrigatório (até 120 caracteres); descrição até 500." };
  }
  return { ok: true, titulo, descricao: descricao || null, publica };
}

export async function criarLista(_anterior: EstadoAcao, form: FormData): Promise<EstadoAcao> {
  const dados = dadosLista(form);
  if (!dados.ok) return { sucesso: false, mensagem: dados.mensagem };
  const token = await tokenAutenticado();
  if (!token) return { sucesso: false, mensagem: "Entre na sua conta para criar uma lista." };
  let idCriado: number;
  try {
    const resposta = await requisitarBackend("/listas", {
      method: "POST",
      headers: { Authorization: `Bearer ${token}` },
      body: JSON.stringify({ titulo: dados.titulo, descricao: dados.descricao, publica: dados.publica }),
    });
    if (!resposta.ok) return { sucesso: false, mensagem: erroStatus(resposta.status) };
    const criado: unknown = await resposta.json();
    if (!criado || typeof criado !== "object" || !("id" in criado) ||
      typeof criado.id !== "number" || !Number.isSafeInteger(criado.id)) {
      return { sucesso: false, mensagem: "Lista criada, mas a API retornou um ID inesperado. Abra Minhas listas." };
    }
    idCriado = criado.id;
  } catch {
    return { sucesso: false, mensagem: "Falha de conexão com a API." };
  }
  revalidatePath("/listas");
  redirect(`/listas/${idCriado}`);
}

export async function editarLista(_anterior: EstadoAcao, form: FormData): Promise<EstadoAcao> {
  const id = idPositivo(form.get("lista_id"));
  const dados = dadosLista(form);
  if (!id || !dados.ok) return { sucesso: false, mensagem: "Dados da lista inválidos." };
  const token = await tokenAutenticado();
  if (!token) return { sucesso: false, mensagem: "Faça login novamente." };
  try {
    const resposta = await requisitarBackend(`/listas/${id}`, {
      method: "PUT",
      headers: { Authorization: `Bearer ${token}` },
      body: JSON.stringify({ titulo: dados.titulo, descricao: dados.descricao, publica: dados.publica }),
    });
    if (!resposta.ok) return { sucesso: false, mensagem: erroStatus(resposta.status) };
    revalidatePath("/listas");
    revalidatePath(`/listas/${id}`);
    return { sucesso: true, mensagem: "Lista atualizada." };
  } catch {
    return { sucesso: false, mensagem: "Falha de conexão com a API." };
  }
}

export async function excluirLista(_anterior: EstadoAcao, form: FormData): Promise<EstadoAcao> {
  const id = idPositivo(form.get("lista_id"));
  if (!id) return { sucesso: false, mensagem: "Lista inválida." };
  const token = await tokenAutenticado();
  if (!token) return { sucesso: false, mensagem: "Faça login novamente." };
  try {
    const resposta = await requisitarBackend(`/listas/${id}`, {
      method: "DELETE",
      headers: { Authorization: `Bearer ${token}` },
    });
    if (!resposta.ok) return { sucesso: false, mensagem: erroStatus(resposta.status) };
  } catch {
    return { sucesso: false, mensagem: "Falha de conexão com a API." };
  }
  revalidatePath("/listas");
  redirect("/listas");
}

export async function adicionarAlbumLista(_anterior: EstadoAcao, form: FormData): Promise<EstadoAcao> {
  const id = idPositivo(form.get("lista_id"));
  const mbid = String(form.get("id_musicbrainz") ?? "").toLowerCase();
  if (!id || !MBID_VALIDO.test(mbid)) {
    return { sucesso: false, mensagem: "Escolha uma lista e um álbum válidos." };
  }
  const token = await tokenAutenticado();
  if (!token) return { sucesso: false, mensagem: "Faça login para adicionar álbuns." };
  try {
    const resposta = await requisitarBackend(`/listas/${id}/itens`, {
      method: "POST",
      headers: { Authorization: `Bearer ${token}` },
      body: JSON.stringify({ obra: { id_musicbrainz: mbid } }),
    });
    if (!resposta.ok) return { sucesso: false, mensagem: erroStatus(resposta.status) };
    revalidatePath(`/listas/${id}`);
    revalidatePath("/listas");
    return { sucesso: true, mensagem: "Álbum adicionado à lista!" };
  } catch {
    return { sucesso: false, mensagem: "Falha de conexão com a API." };
  }
}

export async function removerAlbumLista(_anterior: EstadoAcao, form: FormData): Promise<EstadoAcao> {
  const id = idPositivo(form.get("lista_id"));
  const obra = idPositivo(form.get("obra_id"));
  if (!id || !obra) return { sucesso: false, mensagem: "Álbum inválido." };
  const token = await tokenAutenticado();
  if (!token) return { sucesso: false, mensagem: "Faça login novamente." };
  try {
    const resposta = await requisitarBackend(`/listas/${id}/itens/${obra}`, {
      method: "DELETE",
      headers: { Authorization: `Bearer ${token}` },
    });
    if (!resposta.ok) return { sucesso: false, mensagem: erroStatus(resposta.status) };
    revalidatePath(`/listas/${id}`);
    revalidatePath("/listas");
    return { sucesso: true, mensagem: "Álbum removido da lista." };
  } catch {
    return { sucesso: false, mensagem: "Falha de conexão com a API." };
  }
}

export async function moverAlbumLista(_anterior: EstadoAcao, form: FormData): Promise<EstadoAcao> {
  const id = idPositivo(form.get("lista_id"));
  const obra = idPositivo(form.get("obra_id"));
  const novaPosicao = idPositivo(form.get("nova_posicao"));
  if (!id || !obra || !novaPosicao) return { sucesso: false, mensagem: "Posição inválida." };
  const token = await tokenAutenticado();
  if (!token) return { sucesso: false, mensagem: "Faça login novamente." };
  try {
    const resposta = await requisitarBackend(`/listas/${id}/itens/${obra}`, {
      method: "PATCH",
      headers: { Authorization: `Bearer ${token}` },
      body: JSON.stringify({ nova_posicao: novaPosicao }),
    });
    if (!resposta.ok) return { sucesso: false, mensagem: erroStatus(resposta.status) };
    revalidatePath(`/listas/${id}`);
    return { sucesso: true, mensagem: "Ordem atualizada." };
  } catch {
    return { sucesso: false, mensagem: "Falha de conexão com a API." };
  }
}