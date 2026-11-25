import Link from "next/link";
import { Suspense } from "react";
import { CapaAlbum } from "@/components/capa-album";
import { obterCapaAlbum } from "@/lib/catalogo";
import { consultarDestaques } from "@/lib/feed";
import { catalogoLocal } from "@/lib/exploracao";
import { obterListasPublicas } from "@/lib/listas-publicas";
import { VitrineLista } from "@/components/vitrine-lista";
import { DestaquesMusicais, ReviewsRecentes } from "@/components/feed-musical";
import styles from "./page.module.css";

async function DestaqueReal() {
  // Destaque um registro real que ainda não esteja na vitrine dos mais ouvidos.
  // Se o catálogo tiver poucas obras, usamos a mais ouvida como alternativa.
  const [ouvintes, catalogo] = await Promise.all([
    consultarDestaques("mais-ouvidas"),
    catalogoLocal("", "todos", 1),
  ]);
  const idsEmDestaque = new Set(ouvintes.ok ? ouvintes.dados.map((obra) => obra.id_musicbrainz) : []);
  const obra = (catalogo.ok
    ? catalogo.dados.resultados.find((item) => !idsEmDestaque.has(item.id_musicbrainz))
    : null) ?? (ouvintes.ok ? ouvintes.dados[0] : null);
  if (!obra) {
    return <p className={styles.destaqueVazio}>No featured album yet.</p>;
  }
  const capa = await obterCapaAlbum(obra.id_musicbrainz);
  return (
    <Link className={styles.destaqueObra} href={"/albuns/" + encodeURIComponent(obra.id_musicbrainz)}>
      <CapaAlbum url={capa} titulo={obra.titulo} className={styles.destaqueCapa} />
      <div className={styles.destaqueInfo}>
        
        <span>Featured</span>
        <h2>{obra.titulo}</h2>
        <p>{obra.artista ?? "Unknown artist"}</p>
        
      </div>
    </Link>
  );
}

async function ListasDaComunidade() {
  const resultado = await obterListasPublicas(1);
  if (!resultado.ok) return <section className={styles.descobertaSecao}><h2>Lists</h2><p role="alert" className={styles.message}>{resultado.mensagem}</p></section>;
  return (
    <section className={styles.descobertaSecao} aria-labelledby="listas-comunidade">
      <div className={styles.tituloDescoberta}>
        <h2 id="listas-comunidade">Lists</h2>
        <Link href="/listas/explorar">View all</Link>
      </div>
      {resultado.dados.resultados.length ? <ul className={styles.listasHome}>
        {resultado.dados.resultados.slice(0, 3).map(lista => (
          <li key={lista.id}>
            <Link className={styles.listaCover} href={"/listas/" + lista.id} aria-label={"Open list " + lista.titulo}>
              <VitrineLista listaId={lista.id} titulo={lista.titulo} compacta />
            </Link>
            <div className={styles.listaMeta}>
              <Link className={styles.listaTitle} href={"/listas/" + lista.id}>{lista.titulo}</Link>
              <p><Link href={"/usuarios/" + encodeURIComponent(lista.username)}>{lista.nome_exibicao}</Link> · {lista.total_itens} {lista.total_itens === 1 ? "album" : "albums"}</p>
            </div>
          </li>
        ))}
      </ul> : <p className={styles.message}>No public lists yet.</p>}
    </section>
  );
}

export default function Home() {
  return (
    <main className={`${styles.container} ${styles.editorialHome}`}>
      <section className={styles.hero + " " + styles.heroEditorial} aria-labelledby="titulo-descobrir">
        <div className={styles.heroMain}>
          
          <h1 id="titulo-descobrir">Discover</h1>
          
          <Link className={styles.discoverLink} href="/albuns">Browse albums <span aria-hidden="true">↗</span></Link>
        </div>
        <div className={styles.heroAside}>
          <Suspense fallback={<p className={styles.destaqueVazio}>Loading album…</p>}>
            <DestaqueReal />
          </Suspense>
        </div>
      </section>
      <section className={styles.descobertaSecao} aria-labelledby="mais-ouvidas">
        <div className={styles.shelfInfo}>
          <h2 id="mais-ouvidas">Most played</h2>
          
        </div>
        <Suspense fallback={<p className={styles.message}>Loading albums…</p>}>
          <DestaquesMusicais tipo="mais-ouvidas" />
        </Suspense>
      </section>
      <div className={styles.editorialColumns}>
      <section className={styles.descobertaSecao} aria-labelledby="reviews-recentes">
        <div className={styles.tituloDescoberta}>
          <div className={styles.shelfInfo}>
            <h2 id="reviews-recentes">Reviews</h2>
            
          </div>
          <Link href="/reviews">View all</Link>
        </div>
        <Suspense fallback={<p className={styles.message}>Loading reviews…</p>}>
          <ReviewsRecentes />
        </Suspense>
      </section>
      <Suspense fallback={null}><ListasDaComunidade /></Suspense>
      </div>
    </main>
  );
}
