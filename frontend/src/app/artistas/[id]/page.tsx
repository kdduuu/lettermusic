import Link from "next/link";
import { Suspense } from "react";
import { notFound } from "next/navigation";
import { Paginacao, ResultadosMusicais } from "@/components/exploracao-musical";
import { artista, discografia, obterPagina } from "@/lib/exploracao";
import { MBID_VALIDO } from "@/lib/estado-album";
import styles from "../../page.module.css";

type Props = {
  params: Promise<{ id: string }>;
  searchParams: Promise<{ pagina?: string | string[] }>;
};

async function Conteudo({ params, searchParams }: Props) {
  const { id } = await params;
  if (!MBID_VALIDO.test(id)) notFound();

  const pagina = obterPagina((await searchParams).pagina);
  const perfil = await artista(id);
  if (!perfil.ok) return <p role="alert" className={styles.message}>{perfil.mensagem}</p>;

  const obras = await discografia(id, pagina);

  return (
    <>
      <section className={styles.hero}>
        <h1>{perfil.dados.titulo}</h1>
        <p>{[perfil.dados.tipo, perfil.dados.subtitulo].filter(Boolean).join(" · ")}</p>
      </section>

      <section className={styles.descobertaSecao}>
        <h2>Discografia</h2>
        <p>Álbuns, singles e outros lançamentos vinculados ao artista.</p>
        {obras.ok ? (
          <>
            <ResultadosMusicais itens={obras.dados.resultados} categoria="albuns" />
            <Paginacao pagina={pagina} temProxima={obras.dados.tem_proxima} endereco={`/artistas/${id}`} />
          </>
        ) : <p role="alert" className={styles.message}>{obras.mensagem}</p>}
      </section>
    </>
  );
}

export default function ArtistaPage(props: Props) {
  return (
    <main className={styles.container}>
      <Link href="/">Descobrir</Link>
      <Suspense fallback={<p className={styles.message}>Carregando artista...</p>}>
        <Conteudo {...props} />
      </Suspense>
    </main>
  );
}
