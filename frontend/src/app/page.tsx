import Link from "next/link";
import { Suspense } from "react";
import { SearchForm } from "@/components/site-header";
import { DestaquesMusicais, ReviewsRecentes } from "@/components/feed-musical";
import styles from "./page.module.css";

export default function Home() {
  return (
    <main className={styles.container}>
      <section className={styles.hero}>
        <span className={styles.accent} aria-hidden="true" />
        <h1>Descobrir</h1>
        <p>Encontre álbuns para registrar, avaliar e compartilhar.</p>
        <SearchForm variant="hero" />
      </section>
      <section className={styles.descobertaSecao} aria-labelledby="mais-ouvidas">
        <h2 id="mais-ouvidas">Mais ouvidos</h2>
        <p>Álbuns com mais escutas registradas pela comunidade.</p>
        <Suspense fallback={<p>Carregando álbuns...</p>}>
          <DestaquesMusicais tipo="mais-ouvidas" />
        </Suspense>
      </section>
      <section className={styles.descobertaSecao} aria-labelledby="melhor-avaliadas">
        <h2 id="melhor-avaliadas">Mais bem avaliados</h2>
        <p>Maiores médias das avaliações registradas.</p>
        <Suspense fallback={<p>Carregando álbuns...</p>}>
          <DestaquesMusicais tipo="melhor-avaliadas" />
        </Suspense>
      </section>
      <section className={styles.descobertaSecao} aria-labelledby="reviews-recentes">
        <div className={styles.tituloDescoberta}>
          <h2 id="reviews-recentes">Reviews recentes</h2>
          <Link href="/reviews">Ver todas</Link>
        </div>
        <Suspense fallback={<p>Carregando reviews...</p>}><ReviewsRecentes /></Suspense>
      </section>
    </main>
  );
}