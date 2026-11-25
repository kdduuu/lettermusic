import Link from "next/link";
import { Suspense, type ReactNode } from "react";
import { redirect } from "next/navigation";
import { requisitarBackend } from "@/lib/backend";
import { CapaAlbum } from "@/components/capa-album";
import { obterCapaAlbum } from "@/lib/catalogo";
import { obterTokenSessao, obterUsuarioAutenticado } from "@/lib/sessao";
import styles from "./page.module.css";

type Parametros = Promise<{
  categoria?: string | string[];
  pagina?: string | string[];
}>;

type Registro = {
  id: number;
  obra_id: number;
  id_musicbrainz: string | null;
  titulo: string | null;
  artista: string | null;
  nota?: number;
  texto?: string;
  ouvida_em?: string;
};

type Categoria = {
  titulo: string;
  caminho: string;
  tipo: "ouvidas" | "favoritos" | "quero-ouvir" | "escutas" | "avaliacoes" | "reviews";
};

const CATEGORIAS: Categoria[] = [
  { titulo: "Listened", caminho: "/interacoes/obras-ouvidas", tipo: "ouvidas" },
  { titulo: "Favorites", caminho: "/biblioteca/favoritos", tipo: "favoritos" },
  { titulo: "Want to listen", caminho: "/biblioteca/quero-ouvir", tipo: "quero-ouvir" },
  { titulo: "History", caminho: "/interacoes/escutas", tipo: "escutas" },
  { titulo: "Ratings", caminho: "/interacoes/avaliacoes", tipo: "avaliacoes" },
  { titulo: "Reviews", caminho: "/interacoes/reviews", tipo: "reviews" },
];

async function buscarRegistros(caminho: string, token: string, pagina: number): Promise<Registro[] | null> {
  try {
    const resposta = await requisitarBackend(`${caminho}?pagina=${pagina}&por_pagina=20`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    if (!resposta.ok) return null;
    const dados: unknown = await resposta.json();
    if (!Array.isArray(dados)) return null;
    return dados.filter((item): item is Registro =>
      typeof item === "object" && item !== null &&
      typeof item.id === "number" &&
      typeof item.obra_id === "number" &&
      (item.id_musicbrainz === null || typeof item.id_musicbrainz === "string") &&
      (item.titulo === null || typeof item.titulo === "string") &&
      (item.artista === null || typeof item.artista === "string")
    );
  } catch {
    return null;
  }
}

function Complemento({ registro, tipo }: { registro: Registro; tipo: Categoria["tipo"] }) {
  if (tipo === "avaliacoes" && typeof registro.nota === "number") {
    return <span className={styles.detalhe}>★ {registro.nota.toLocaleString("en-US")}</span>;
  }
  if (tipo === "reviews" && typeof registro.texto === "string") {
    return <p className={styles.reviewTexto}>{registro.texto}</p>;
  }
  if (tipo === "escutas" && typeof registro.ouvida_em === "string") {
    const data = new Date(registro.ouvida_em);
    return !Number.isNaN(data.getTime()) ? (
      <span className={styles.detalhe}>
        {new Intl.DateTimeFormat("en-US", { dateStyle: "short", timeZone: "America/Sao_Paulo" }).format(data)}
      </span>
    ) : null;
  }
  return null;
}

function AlbumLink({ registro, children }: { registro: Registro; children: ReactNode }) {
  const id = registro.id_musicbrainz;
  return id && /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i.test(id)
    ? <Link href={"/albuns/" + encodeURIComponent(id)} className={styles.albumVitrine}>{children}</Link>
    : <div className={styles.albumVitrine}>{children}</div>;
}

async function Collection({ registros, tipo }: { registros: Registro[]; tipo: Categoria["tipo"] }) {
  const ids = [...new Set(registros.flatMap(r => r.id_musicbrainz ? [r.id_musicbrainz] : []))];
  const capas = new Map(await Promise.all(ids.map(async id => [id, await obterCapaAlbum(id)] as const)));
  const textual = tipo === "reviews" || tipo === "escutas";
  return (
    <ul className={textual ? styles.diary : styles.collection}>
      {registros.map(registro => (
        <li key={registro.id}>
          <AlbumLink registro={registro}>
            <CapaAlbum url={capas.get(registro.id_musicbrainz ?? "") ?? null}
              titulo={registro.titulo ?? "Album"} className={styles.capaVitrine} />
            <div className={styles.collectionInfo}>
              <strong>{registro.titulo ?? "Untitled album"}</strong>
              <span>{registro.artista ?? "Unknown artist"}</span>
            </div>
          </AlbumLink>
          <Complemento registro={registro} tipo={tipo} />
        </li>
      ))}
    </ul>
  );
}

async function ConteudoBiblioteca({ searchParams }: { searchParams: Parametros }) {
  const [usuario, token, parametros] = await Promise.all([
    obterUsuarioAutenticado(), obterTokenSessao(), searchParams,
  ]);
  if (!usuario || !token) redirect("/entrar");
  const categoria = CATEGORIAS.find(c => c.tipo === parametros.categoria) ?? CATEGORIAS[0];
  const numero = typeof parametros.pagina === "string" ? parametros.pagina : "";
  const pagina = /^[1-9]\d{0,4}$/.test(numero) ? Math.min(10000, Number(numero)) : 1;
  const itens = await buscarRegistros(categoria.caminho, token, pagina);
  const base = "/biblioteca?categoria=" + categoria.tipo + "&pagina=";

  return (
    <>
      <header className={styles.libraryHeader}>
        <h1>Library</h1>
        <Link href={"/usuarios/" + encodeURIComponent(usuario.username)}>Profile</Link>
      </header>
      <nav className={styles.libraryTabs} aria-label="Library categories">
        {CATEGORIAS.map(c => (
          <Link key={c.tipo} href={"/biblioteca?categoria=" + c.tipo}
            aria-current={c.tipo === categoria.tipo ? "page" : undefined}>{c.titulo}</Link>
        ))}
      </nav>
      <section className={styles.libraryContent} aria-label={categoria.titulo}>
        {itens === null ? <p role="alert" className={styles.mensagem}>Unable to load your collection. Please try again.</p>
          : !itens.length ? <p className={styles.mensagem}>Nothing here yet.</p>
          : <Suspense fallback={<p className={styles.mensagem}>Loading covers…</p>}>
              <Collection registros={itens} tipo={categoria.tipo} />
            </Suspense>}
        {itens !== null && (pagina > 1 || itens.length === 20) ? (
          <nav className={styles.paginacao} aria-label="Library pages">
            {pagina > 1 ? <Link href={base + (pagina - 1)}>Previous</Link> : null}
            <span>Page {pagina}</span>
            {itens.length === 20 && pagina < 10000 ? <Link href={base + (pagina + 1)}>Next</Link> : null}
          </nav>
        ) : null}
      </section>
    </>
  );
}

export default function BibliotecaPage({
  searchParams,
}: {
  searchParams: Parametros;
}) {
  return (
    <main className={styles.container}>
      <Suspense fallback={<p className={styles.mensagem}>Loading library…</p>}>
        <ConteudoBiblioteca searchParams={searchParams} />
      </Suspense>
    </main>
  );
}