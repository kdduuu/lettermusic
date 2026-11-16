import Link from "next/link";
import { Suspense } from "react";
import { CapaAlbum } from "@/components/capa-album";
import { FormularioInteracoes } from "@/components/formulario-interacoes";
import { detalharAlbum, obterCapaAlbum } from "@/lib/catalogo";
import { obterUsuarioAutenticado } from "@/lib/sessao";
import styles from "./page.module.css";

type ParametrosAlbum = Promise<{ id: string }>;

async function CapaDaObra({ id, titulo }: { id: string; titulo: string }) {
  const url = await obterCapaAlbum(id);
  return <CapaAlbum key={id} url={url} titulo={titulo} className={styles.cover} />;
}

async function ConteudoAlbum({ params }: { params: ParametrosAlbum }) {
  const { id } = await params;
  const resultado = await detalharAlbum(id);

  if (!resultado.ok) {
    return <p className={styles.message} role="alert">{resultado.mensagem}</p>;
  }

  const { obra } = resultado;
  const usuario = await obterUsuarioAutenticado();
  return (
    <article className={styles.album}>
      <Suspense fallback={<div className={styles.cover} aria-label="Carregando capa">♪</div>}>
        <CapaDaObra id={id} titulo={obra.titulo ?? "Álbum"} />
      </Suspense>
      <div className={styles.info}>
        <span className={styles.accent} aria-hidden="true" />
        <h1>{obra.titulo}</h1>
        <p className={styles.artist}>{obra.artista ?? "Artista não informado"}</p>
        <p className={styles.meta}>
          {[obra.data_lancamento?.slice(0, 4), obra.tipo].filter(Boolean).join(" · ")}
        </p>
        {usuario ? (
          <FormularioInteracoes id={id} />
        ) : (
          <p className={styles.convite}>
            <Link href="/entrar">Entre</Link> para registrar, favoritar ou adicionar à sua biblioteca.
          </p>
        )}
      </div>
    </article>
  );
}

export default function AlbumPage({ params }: { params: ParametrosAlbum }) {
  return (
    <main className={styles.container}>
      <Link href="/" className={styles.back}>Início</Link>
      <Suspense fallback={<p className={styles.message}>Carregando álbum...</p>}>
        <ConteudoAlbum params={params} />
      </Suspense>
    </main>
  );
}