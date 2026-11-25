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

async function DestaquesEditoriais() {
  const [populares, catalogo] = await Promise.all([
    consultarDestaques("mais-ouvidas"), catalogoLocal("", "todos", 1),
  ]);
  const popularesIds = new Set(populares.ok ? populares.dados.map(o => o.id_musicbrainz) : []);
  const obras = catalogo.ok ? catalogo.dados.resultados : [];
  const candidatos = [...obras.filter(o => !popularesIds.has(o.id_musicbrainz)), ...obras, ...(populares.ok ? populares.dados : [])];
  const selecionados = [...new Map(candidatos.map(o => [o.id_musicbrainz, o])).values()].slice(0, 3);
  if (!selecionados.length) return <p className={styles.message}>{catalogo.ok ? "No albums yet." : catalogo.mensagem}</p>;
  const capas = await Promise.all(selecionados.map(o => obterCapaAlbum(o.id_musicbrainz)));
  return <div className={styles.featureGrid} data-count={selecionados.length}>
    {selecionados.map((obra,i) => <Link className={styles.featureCard} key={obra.id_musicbrainz} href={"/albuns/" + encodeURIComponent(obra.id_musicbrainz)}>
      <CapaAlbum url={capas[i]} titulo={obra.titulo} className={styles.featureArt} />
      <div className={styles.featureCopy}><h2>{obra.titulo}</h2><p>{obra.artista ?? "Unknown artist"}</p></div>
    </Link>)}
  </div>;
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
  return <main className={styles.container + " " + styles.magazineHome}>
    <header className={styles.magazineHeader}>
      <h1>Discover</h1>
      <Link href="/albuns" className={styles.discoverLink}>Browse albums ↗</Link>
    </header>
    <section aria-label="Featured albums">
      <Suspense fallback={<p className={styles.message}>Loading albums…</p>}><DestaquesEditoriais /></Suspense>
    </section>
    <section className={styles.magazineSection} aria-labelledby="mais-ouvidas">
      <div className={styles.tituloDescoberta}><h2 id="mais-ouvidas">Most played</h2></div>
      <Suspense fallback={<p className={styles.message}>Loading albums…</p>}><DestaquesMusicais tipo="mais-ouvidas" /></Suspense>
    </section>
    <div className={styles.editorialColumns + " " + styles.socialCards}>
      <section className={styles.magazineSection} aria-labelledby="reviews-recentes">
        <div className={styles.tituloDescoberta}><h2 id="reviews-recentes">Reviews</h2><Link href="/reviews">View all ↗</Link></div>
        <Suspense fallback={<p className={styles.message}>Loading reviews…</p>}><ReviewsRecentes /></Suspense>
      </section>
      <Suspense fallback={<p className={styles.message}>Loading lists…</p>}><ListasDaComunidade /></Suspense>
    </div>
  </main>;
}
