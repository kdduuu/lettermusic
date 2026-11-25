"use server";

import { revalidatePath } from "next/cache";
import { requisitarBackend } from "@/lib/backend";
import { buscar } from "@/lib/exploracao";
import { MBID_VALIDO } from "@/lib/estado-album";
import { obterTokenSessao } from "@/lib/sessao";
import type { AlbumFavorito } from "@/lib/perfis";
import type { EstadoAcao } from "@/lib/estado-acoes";

type BuscaFavoritos = { albuns: AlbumFavorito[]; mensagem: string };

export async function buscarFavoritosPerfil(_estado: BuscaFavoritos, form: FormData): Promise<BuscaFavoritos> {
  const termo = String(form.get("termo") ?? "").trim();
  if (termo.length < 2 || termo.length > 100) {
    return { albuns: [], mensagem: "Enter 2 to 100 characters." };
  }
  if (!await obterTokenSessao()) return { albuns: [], mensagem: "Sign in again." };
  const resultado = await buscar(termo, "albuns", 1, 12);
  if (!resultado.ok) return { albuns: [], mensagem: resultado.mensagem };
  const albuns = resultado.dados.resultados
    .filter(item => item.tipo?.toLowerCase() === "album")
    .map(({id_musicbrainz,titulo,artista}) => ({id_musicbrainz,titulo,artista}));
  return { albuns, mensagem: albuns.length ? "" : "No albums found." };
}

export async function salvarFavoritosPerfil(_estado: EstadoAcao, form: FormData): Promise<EstadoAcao> {
  const albuns = form.getAll("album").map(id => String(id).toLowerCase());
  if (albuns.length > 4 || new Set(albuns).size !== albuns.length || !albuns.every(id => MBID_VALIDO.test(id))) {
    return { sucesso: false, mensagem: "Choose up to four different albums." };
  }
  const token = await obterTokenSessao();
  if (!token) return { sucesso: false, mensagem: "Sign in again." };
  try {
    const resposta = await requisitarBackend("/auth/perfil/favoritos", {
      method: "PUT",
      headers: { Authorization: `Bearer ${token}` },
      body: JSON.stringify({ albuns }),
    });
    if (!resposta.ok) return {
      sucesso: false,
      mensagem: resposta.status === 401 ? "Session expired. Sign in again." :
        resposta.status === 422 ? "Choose valid albums." :
        resposta.status === 404 ? "Album not found." :
        resposta.status === 502 ? "Music catalog temporarily unavailable." : "Unable to save favorites.",
    };
  } catch {
    return { sucesso: false, mensagem: "Connection failed. Try again." };
  }
  revalidatePath("/usuarios/[username]", "page");
  return { sucesso: true, mensagem: "Saved." };
}
