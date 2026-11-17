// Leitura publica de perfis. Executar somente no servidor Next.js.
import { requisitarBackend } from "@/lib/backend";

export type AlbumRecente = {
  id_musicbrainz: string;
  titulo: string;
  artista: string | null;
  registrado_em: string;
};

export type ReviewRecente = {
  id: number;
  id_musicbrainz: string;
  titulo: string;
  artista: string | null;
  texto: string;
  criada_em: string;
};

export type ListaRecente = {
  id: number;
  titulo: string;
  descricao: string | null;
  criada_em: string;
};

export type PerfilSocial = {
  id: number;
  username: string;
  nome_exibicao: string;
  bio: string | null;
  criado_em: string;
  estatisticas: {
    avaliacoes: number;
    reviews: number;
    listas_publicas: number;
  };
  albuns_recentes: AlbumRecente[];
  reviews_recentes: ReviewRecente[];
  listas_publicas: ListaRecente[];
};

type ResultadoPerfil =
  | { ok: true; perfil: PerfilSocial }
  | { ok: false; status: number; mensagem: string };

function objeto(valor: unknown): valor is Record<string, unknown> {
  return typeof valor === "object" && valor !== null && !Array.isArray(valor);
}

function perfilValido(valor: unknown): valor is PerfilSocial {
  if (!objeto(valor) || !objeto(valor.estatisticas)) return false;
  const e = valor.estatisticas;
  return (
    typeof valor.id === "number" &&
    typeof valor.username === "string" &&
    typeof valor.nome_exibicao === "string" &&
    (valor.bio === null || typeof valor.bio === "string") &&
    typeof e.avaliacoes === "number" &&
    typeof e.reviews === "number" &&
    typeof e.listas_publicas === "number" &&
    Array.isArray(valor.albuns_recentes) &&
    valor.albuns_recentes.every((album: unknown) =>
      objeto(album) && typeof album.id_musicbrainz === "string" &&
      typeof album.titulo === "string" &&
      (album.artista === null || typeof album.artista === "string")
    ) &&
    Array.isArray(valor.reviews_recentes) &&
    valor.reviews_recentes.every((review: unknown) =>
      objeto(review) && typeof review.id === "number" &&
      typeof review.id_musicbrainz === "string" &&
      typeof review.titulo === "string" && typeof review.texto === "string"
    ) &&
    Array.isArray(valor.listas_publicas) &&
    valor.listas_publicas.every((lista: unknown) =>
      objeto(lista) && typeof lista.id === "number" &&
      typeof lista.titulo === "string" &&
      (lista.descricao === null || typeof lista.descricao === "string")
    )
  );
}

export async function consultarPerfilPublico(username: string): Promise<ResultadoPerfil> {
  if (!/^[a-zA-Z0-9_]{3,30}$/.test(username)) {
    return { ok: false, status: 404, mensagem: "Perfil não encontrado." };
  }

  try {
    const resposta = await requisitarBackend(
      `/usuarios/${encodeURIComponent(username)}/social`,
    );
    if (!resposta.ok) {
      return {
        ok: false,
        status: resposta.status,
        mensagem: resposta.status === 404
          ? "Perfil não encontrado."
          : "Não foi possível consultar este perfil agora.",
      };
    }

    const dados: unknown = await resposta.json();
    if (!perfilValido(dados)) {
      return { ok: false, status: 502, mensagem: "Resposta inesperada da API de perfis." };
    }
    return { ok: true, perfil: dados };
  } catch {
    return {
      ok: false,
      status: 503,
      mensagem: "API indisponível. Verifique se o FastAPI está ligado.",
    };
  }
}