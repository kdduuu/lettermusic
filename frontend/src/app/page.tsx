import Link from "next/link";
import { Suspense } from "react";
import { CapaAlbum } from "@/components/capa-album";
import { obterCapaAlbum } from "@/lib/catalogo";
import { consultarDestaques } from "@/lib/feed";
import { catalogoLocal } from "@/lib/exploracao";
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
    return <p className={styles.destaqueVazio}>Sem destaques.</p>;
  }
  const capa = await obterCapaAlbum(obra.id_musicbrainz);
  return (
    <Link className={styles.destaqueObra} href={"/albuns/" + encodeURIComponent(obra.id_musicbrainz)}>
      <CapaAlbum url={capa} titulo={obra.titulo} className={styles.destaqueCapa} />
      <div className={styles.destaqueInfo}>
        
        <h2>{obra.titulo}</h2>
        <p>{obra.artista ?? "Artista não informado"}</p>
        
      </div>
    </Link>
  );
}

async function AvaliacoesSignificativas() {
  const resultado = await consultarDestaques("melhor-avaliadas");
  if (!resultado.ok) return null;
  const obras = resultado.dados;
  // Se todas as notas forem iguais ou a amostra for muito pequena,
  // não repetimos a mesma vitrine sob outro título.
  if (obras.length < 4 || new Set(obras.map((obra) => obra.media)).size < 2) return null;
  return (
    <section className={styles.secaoRankings} aria-labelledby="melhor-avaliadas">
      <div className={styles.shelfInfo}>
        <h2 id="melhor-avaliadas">Mais bem avaliados</h2>
      </div>
      <ul className={styles.avaliacoesLista}>
        {obras.map((obra) => (
          <li key={obra.obra_id}>
            <div>
              <Link href={"/albuns/" + encodeURIComponent(obra.id_musicbrainz)}>{obra.titulo}</Link>
              <span>{obra.artista ?? "Artista não informado"}</span>
            </div>
            <strong aria-label={"Nota " + (obra.media ?? 0).toLocaleString("pt-BR") + " de 5"}>
              ★ {(obra.media ?? 0).toLocaleString("pt-BR", { maximumFractionDigits: 1 })}
            </strong>
          </li>
        ))}
      </ul>
    </section>
  );
}

export default function Home() {
  return (
    <main className={styles.container}>
      <section className={styles.hero + " " + styles.heroEditorial} aria-labelledby="titulo-descobrir">
        <div className={styles.heroMain}>
          
          <h1 id="titulo-descobrir">Descobrir</h1>
          
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
      <Suspense fallback={null}>
        <AvaliacoesSignificativas />
      </Suspense>
      <section className={styles.descobertaSecao} aria-labelledby="reviews-recentes">
        <div className={styles.tituloDescoberta}>
          <div className={styles.shelfInfo}>
            <h2 id="reviews-recentes">Reviews recentes</h2>
            
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
