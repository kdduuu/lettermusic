"use server";

import { revalidatePath } from "next/cache";
import { redirect } from "next/navigation";
import { requisitarBackend } from "@/lib/backend";
import { MBID_VALIDO } from "@/lib/estado-album";
import { idPositivo } from "@/lib/listas";
import { obterTokenSessao } from "@/lib/sessao";
import type { EstadoAcao } from "@/lib/estado-acoes";

function erroStatus(status: number): string {
  if (status === 401) return "Session expired. Sign in again.";
  if (status === 403 || status === 404) return "List or item unavailable for this account.";
  if (status === 409) return "This album is already in the list.";
  if (status === 422) return "Invalid details. Check the form.";
  if (status === 502) return "Music catalog temporarily unavailable.";
  return "Unable to complete the action.";
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
    return { ok: false, mensagem: "Title required (up to 120 characters); description up to 500." };
  }
  return { ok: true, titulo, descricao: descricao || null, publica };
}

export async function criarLista(_anterior: EstadoAcao, form: FormData): Promise<EstadoAcao> {
  const dados = dadosLista(form);
  if (!dados.ok) return { sucesso: false, mensagem: dados.mensagem };
  const token = await tokenAutenticado();
  if (!token) return { sucesso: false, mensagem: "Sign in to create a list." };
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
      return { sucesso: false, mensagem: "List created, but the service returned an unexpected ID. Open My lists." };
    }
    idCriado = criado.id;
  } catch {
    return { sucesso: false, mensagem: "Connection failed. Try again." };
  }
  revalidatePath("/listas");
  redirect(`/listas/${idCriado}`);
}

export async function editarLista(_anterior: EstadoAcao, form: FormData): Promise<EstadoAcao> {
  const id = idPositivo(form.get("lista_id"));
  const dados = dadosLista(form);
  if (!id || !dados.ok) return { sucesso: false, mensagem: "Invalid list details." };
  const token = await tokenAutenticado();
  if (!token) return { sucesso: false, mensagem: "Sign in again." };
  try {
    const resposta = await requisitarBackend(`/listas/${id}`, {
      method: "PUT",
      headers: { Authorization: `Bearer ${token}` },
      body: JSON.stringify({ titulo: dados.titulo, descricao: dados.descricao, publica: dados.publica }),
    });
    if (!resposta.ok) return { sucesso: false, mensagem: erroStatus(resposta.status) };
    revalidatePath("/listas");
    revalidatePath(`/listas/${id}`);
    return { sucesso: true, mensagem: "List updated." };
  } catch {
    return { sucesso: false, mensagem: "Connection failed. Try again." };
  }
}

export async function excluirLista(_anterior: EstadoAcao, form: FormData): Promise<EstadoAcao> {
  const id = idPositivo(form.get("lista_id"));
  if (!id) return { sucesso: false, mensagem: "Invalid list." };
  const token = await tokenAutenticado();
  if (!token) return { sucesso: false, mensagem: "Sign in again." };
  try {
    const resposta = await requisitarBackend(`/listas/${id}`, {
      method: "DELETE",
      headers: { Authorization: `Bearer ${token}` },
    });
    if (!resposta.ok) return { sucesso: false, mensagem: erroStatus(resposta.status) };
  } catch {
    return { sucesso: false, mensagem: "Connection failed. Try again." };
  }
  revalidatePath("/listas");
  redirect("/listas");
}

export async function adicionarAlbumLista(_anterior: EstadoAcao, form: FormData): Promise<EstadoAcao> {
  const id = idPositivo(form.get("lista_id"));
  const mbid = String(form.get("id_musicbrainz") ?? "").toLowerCase();
  if (!id || !MBID_VALIDO.test(mbid)) {
    return { sucesso: false, mensagem: "Choose a valid list and album." };
  }
  const token = await tokenAutenticado();
  if (!token) return { sucesso: false, mensagem: "Sign in to add albums." };
  try {
    const resposta = await requisitarBackend(`/listas/${id}/itens`, {
      method: "POST",
      headers: { Authorization: `Bearer ${token}` },
      body: JSON.stringify({ obra: { id_musicbrainz: mbid } }),
    });
    if (!resposta.ok) return { sucesso: false, mensagem: erroStatus(resposta.status) };
    revalidatePath(`/listas/${id}`);
    revalidatePath("/listas");
    return { sucesso: true, mensagem: "Album added to list." };
  } catch {
    return { sucesso: false, mensagem: "Connection failed. Try again." };
  }
}

export async function removerAlbumLista(_anterior: EstadoAcao, form: FormData): Promise<EstadoAcao> {
  const id = idPositivo(form.get("lista_id"));
  const obra = idPositivo(form.get("obra_id"));
  if (!id || !obra) return { sucesso: false, mensagem: "Invalid album." };
  const token = await tokenAutenticado();
  if (!token) return { sucesso: false, mensagem: "Sign in again." };
  try {
    const resposta = await requisitarBackend(`/listas/${id}/itens/${obra}`, {
      method: "DELETE",
      headers: { Authorization: `Bearer ${token}` },
    });
    if (!resposta.ok) return { sucesso: false, mensagem: erroStatus(resposta.status) };
    revalidatePath(`/listas/${id}`);
    revalidatePath("/listas");
    return { sucesso: true, mensagem: "Album removed from list." };
  } catch {
    return { sucesso: false, mensagem: "Connection failed. Try again." };
  }
}

export async function moverAlbumLista(_anterior: EstadoAcao, form: FormData): Promise<EstadoAcao> {
  const id = idPositivo(form.get("lista_id"));
  const obra = idPositivo(form.get("obra_id"));
  const novaPosicao = idPositivo(form.get("nova_posicao"));
  if (!id || !obra || !novaPosicao) return { sucesso: false, mensagem: "Invalid position." };
  const token = await tokenAutenticado();
  if (!token) return { sucesso: false, mensagem: "Sign in again." };
  try {
    const resposta = await requisitarBackend(`/listas/${id}/itens/${obra}`, {
      method: "PATCH",
      headers: { Authorization: `Bearer ${token}` },
      body: JSON.stringify({ nova_posicao: novaPosicao }),
    });
    if (!resposta.ok) return { sucesso: false, mensagem: erroStatus(resposta.status) };
    revalidatePath(`/listas/${id}`);
    return { sucesso: true, mensagem: "Order updated." };
  } catch {
    return { sucesso: false, mensagem: "Connection failed. Try again." };
  }
}