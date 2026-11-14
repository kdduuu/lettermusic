import Link from "next/link";
import { Suspense } from "react";
import { detalharAlbum } from "@/lib/catalogo";
import styles from "./page.module.css";

type ParametrosAlbum = Promise<{ id: string }>;

async function ConteudoAlbum({ params }: { params: ParametrosAlbum }) {
  const { id } = await params;
  const resultado = await detalharAlbum(id);

  if (!resultado.ok) {
    return <p className={styles.message} role="alert">{resultado.mensagem}</p>;
  }

  const { obra } = resultado;
  return (
    <article className={styles.album}>
      <div className={styles.cover} aria-label="Capa ainda não disponível">♪</div>
      <div className={styles.info}>
        <span className={styles.accent} aria-hidden="true" />
        <h1>{obra.titulo}</h1>
        <p className={styles.artist}>{obra.artista ?? "Artista não informado"}</p>
        <p className={styles.meta}>
          {[obra.data_lancamento?.slice(0, 4), obra.tipo].filter(Boolean).join(" · ")}
        </p>
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