import Link from "next/link";
import { Suspense } from "react";
import { CardsReviews } from "@/components/feed-musical";
import { consultarFeedReviews } from "@/lib/feed";
import styles from "./page.module.css";

type Parametros = Promise<{ pagina?: string | string[] }>;

function obterPagina(valor: string | string[] | undefined): number {
  if (typeof valor !== "string" || !/^\d+$/.test(valor)) return 1;
  const pagina = Number(valor);
  return Number.isSafeInteger(pagina) && pagina >= 1 && pagina <= 10000 ? pagina : 1;
}

async function ConteudoReviews({ searchParams }: { searchParams: Parametros }) {
  const pagina = obterPagina((await searchParams).pagina);
  const resultado = await consultarFeedReviews(pagina, 12);
  if (!resultado.ok) return <p role="alert" className={styles.mensagem}>{resultado.mensagem}</p>;
  const { dados } = resultado;
  return (
    <>
      <CardsReviews reviews={dados.resultados} />
      <nav className={styles.paginacao} aria-label="Páginas de reviews">
        {pagina > 1 ? <Link href={`/reviews?pagina=${pagina - 1}`}>Anterior</Link> : null}
        <span>Página {pagina}</span>
        {dados.tem_proxima && pagina < 10000 ? <Link href={`/reviews?pagina=${pagina + 1}`}>Próxima</Link> : null}
      </nav>
    </>
  );
}

export default function ReviewsPage({ searchParams }: { searchParams: Parametros }) {
  return (
    <main className={styles.container}>
      <header>
        <h1>Reviews</h1>
        <p>Descubra o que a comunidade está ouvindo e compartilhando.</p>
      </header>
      <Suspense fallback={<p className={styles.mensagem}>Carregando reviews...</p>}>
        <ConteudoReviews searchParams={searchParams} />
      </Suspense>
    </main>
  );
}