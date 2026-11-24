import Link from "next/link";
import { Suspense } from "react";
import { SearchForm } from "@/components/site-header";
import { CapaAlbum } from "@/components/capa-album";
import { obterCapaAlbum } from "@/lib/catalogo";
import { consultarDestaques } from "@/lib/feed";
import { DestaquesMusicais, ResumoBemAvaliados, ReviewsRecentes } from "@/components/feed-musical";
import styles from "./page.module.css";

async function DestaqueReal() {
  const resultado = await consultarDestaques("mais-ouvidas");
  const obra = resultado.ok ? resultado.dados[0] : null;
  if (!obra) {
    return <p className={styles.destaqueVazio}>As descobertas da comunidade aparecem aqui quando houver registros públicos.</p>;
  }
  const capa = await obterCapaAlbum(obra.id_musicbrainz);
  return (
    <Link className={styles.destaqueObra} href={"/albuns/" + encodeURIComponent(obra.id_musicbrainz)}>
      <CapaAlbum url={capa} titulo={obra.titulo} className={styles.destaqueCapa} />
      <div className={styles.destaqueInfo}>
        <span>Entre os mais ouvidos</span>
        <h2>{obra.titulo}</h2>
        <p>{obra.artista ?? "Artista não informado"}</p>
        
      </div>
    </Link>
  );
}

export default function Home() {
  return (
    <main className={styles.container}>
      <section className={styles.hero + " " + styles.heroEditorial} aria-labelledby="titulo-descobrir">
        <div className={styles.heroMain}>
          <p className={styles.heroEyebrow}>LETTERMUSIC / MÚSICA</p>
          <h1 id="titulo-descobrir">Descobrir</h1>
          <p>Encontre seu próximo disco.</p>
          <SearchForm variant="hero" />
          <div className={styles.heroLinks}>
            <Link href="/albuns">Explorar álbuns ↗</Link>
            <Link href="/listas/explorar">Listas da comunidade ↗</Link>
          </div>
        </div>
        <div className={styles.heroAside}>
          <Suspense fallback={<p className={styles.destaqueVazio}>Carregando destaque musical...</p>}>
            <DestaqueReal />
          </Suspense>
        </div>
      </section>
      <section className={styles.descobertaSecao} aria-labelledby="mais-ouvidas">
        <div className={styles.shelfInfo}>
          <h2 id="mais-ouvidas">Mais ouvidos</h2>
          
        </div>
        <Suspense fallback={<p className={styles.message}>Carregando álbuns...</p>}>
          <DestaquesMusicais tipo="mais-ouvidas" />
        </Suspense>
      </section>
      <section className={styles.secaoRankings} aria-labelledby="melhor-avaliadas">
        <div className={styles.shelfInfo}>
          
          <h2 id="melhor-avaliadas">Mais bem avaliados</h2>
          
        </div>
        <Suspense fallback={<p className={styles.message}>Carregando avaliações...</p>}>
          <ResumoBemAvaliados />
        </Suspense>
      </section>
      <section className={styles.descobertaSecao} aria-labelledby="reviews-recentes">
        <div className={styles.tituloDescoberta}>
          <div className={styles.shelfInfo}>
            <h2 id="reviews-recentes">O que andam dizendo</h2>
            
          </div>
          <Link href="/reviews">Todas as reviews ↗</Link>
        </div>
        <Suspense fallback={<p className={styles.message}>Carregando reviews...</p>}>
          <ReviewsRecentes />
        </Suspense>
      </section>
    </main>
  );
}
