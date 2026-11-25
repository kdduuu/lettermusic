import Link from "next/link";
import { notFound } from "next/navigation";
import { Suspense } from "react";
import { CapaAlbum } from "@/components/capa-album";
import { VitrineLista } from "@/components/vitrine-lista";
import { FavoritosPerfil } from "@/components/favoritos-perfil";
import { obterUsuarioAutenticado } from "@/lib/sessao";
import { obterCapaAlbum } from "@/lib/catalogo";
import { consultarPerfilPublico, type AlbumRecente, type ReviewRecente } from "@/lib/perfis";
import styles from "./page.module.css";

type ParametrosPerfil = Promise<{ username: string }>;

function anoCadastro(data: string): string {
  const ano = Number(data.slice(0, 4));
  return ano >= 2000 && ano <= 2100 ? String(ano) : "";
}
function dataResumida(data: string): string {
  const partes = /^(\d{4})-(\d{2})-(\d{2})/.exec(data);
  return partes ? partes[1] + "-" + partes[2] + "-" + partes[3] : "";
}

async function CapasRecentes({ albuns }: { albuns: AlbumRecente[] }) {
  const urls = await Promise.all(albuns.map((album) => obterCapaAlbum(album.id_musicbrainz)));
  return (
    <div className={styles.gradeCapas} data-count={albuns.length}>
      {albuns.map((album, indice) => (
        <Link
          key={album.id_musicbrainz}
          href={"/albuns/" + encodeURIComponent(album.id_musicbrainz)}
          className={styles.itemCapa}
          title={album.titulo + " — " + (album.artista ?? "Unknown artist")}
        >
          <CapaAlbum url={urls[indice]} titulo={album.titulo} className={styles.capa} />
          <span className={styles.nomeAlbum}>{album.titulo}</span>
          <span className={styles.artistaAlbum}>{album.artista ?? "Unknown artist"}</span>
        </Link>
      ))}
    </div>
  );
}


async function ReviewsPerfil({ reviews }: { reviews: ReviewRecente[] }) {
  const urls = await Promise.all(reviews.map(review => obterCapaAlbum(review.id_musicbrainz)));
  return (
    <ul className={styles.feed}>
      {reviews.map((review, indice) => (
        <li key={review.id} className={styles.itemReview}>
          <Link href={"/albuns/" + encodeURIComponent(review.id_musicbrainz)} className={styles.linkCapaReview} aria-label={"Open " + review.titulo}>
            <CapaAlbum url={urls[indice]} titulo={review.titulo} className={styles.capaReview} />
          </Link>
          <div className={styles.conteudoReview}>
            <div className={styles.reviewTopo}>
              <Link href={"/albuns/" + encodeURIComponent(review.id_musicbrainz)} className={styles.reviewAlbum}>{review.titulo}</Link>
              <time dateTime={review.criada_em}>{dataResumida(review.criada_em)}</time>
            </div>
            <p className={styles.reviewArtista}>{review.artista ?? "Unknown artist"}</p>
            <p className={styles.reviewTexto}>{review.texto}</p>

          </div>
        </li>
      ))}
    </ul>
  );
}

async function ConteudoPerfil({ params }: { params: ParametrosPerfil }) {
  const { username } = await params;
  const [resultado, usuario] = await Promise.all([consultarPerfilPublico(username), obterUsuarioAutenticado()]);
  if (!resultado.ok) {
    if (resultado.status === 404) notFound();
    return <p role="alert" className={styles.erro}>{resultado.mensagem}</p>;
  }
  const { perfil } = resultado;
  const inicial = Array.from(perfil.nome_exibicao.trim()).slice(0, 1).join("").toLocaleUpperCase("en-US") || "♪";
  const ano = anoCadastro(perfil.criado_em);

  return (
    <>
      <header className={styles.perfilHero}>
        <div className={styles.identidade}>
          <div className={styles.avatar} aria-label={"Initial of " + perfil.nome_exibicao} role="img">{inicial}</div>
          <div className={styles.informacoes}>
            {ano ? <p className={styles.sobretitulo}>Since {ano}</p> : null}
            <h1>{perfil.nome_exibicao}</h1>
            <p className={styles.username}>@{perfil.username}</p>
            {perfil.bio ? <p className={styles.bio}>{perfil.bio}</p> : null}
          </div>
        </div>
        <dl className={styles.estatisticas} aria-label="Public profile activity">
          <div><dd>{perfil.estatisticas.avaliacoes}</dd><dt>Ratings</dt></div>
          <div><dd>{perfil.estatisticas.reviews}</dd><dt>Reviews</dt></div>
          <div><dd>{perfil.estatisticas.listas_publicas}</dd><dt>Public lists</dt></div>
        </dl>
      </header>

      {(perfil.albuns_favoritos.length > 0 || usuario?.id === perfil.id) ? (
        <FavoritosPerfil
          key={perfil.albuns_favoritos.map(album => album.id_musicbrainz).join(",")}
          albuns={perfil.albuns_favoritos}
          dono={usuario?.id === perfil.id}
        />
      ) : null}

      <section className={styles.discografia} aria-labelledby="albuns-recentes">
        <div className={styles.tituloSecao}>
          <div>
            
            <h2 id="albuns-recentes">Recent activity</h2>
          </div>
          
        </div>
        {perfil.albuns_recentes.length ? (
          <Suspense fallback={<p className={styles.vazio}>Loading covers…</p>}>
            <CapasRecentes albuns={perfil.albuns_recentes} />
          </Suspense>
        ) : <p className={styles.vazio}>No recent activity.</p>}
      </section>

      <div className={styles.corpoEditorial}>
        <section className={styles.reviews} aria-labelledby="reviews-recentes">
          <div className={styles.tituloSecao}>
            <div>
              
              <h2 id="reviews-recentes">Reviews</h2>
            </div>
          </div>
          {perfil.reviews_recentes.length ? (
            <Suspense fallback={<p className={styles.vazio}>Loading reviews…</p>}>
              <ReviewsPerfil reviews={perfil.reviews_recentes} />
            </Suspense>
          ) : <p className={styles.vazio}>No reviews yet.</p>}
        </section>

        <aside className={styles.listas} aria-labelledby="listas-publicas">
          <div className={styles.tituloSecao}>
            <div>
              
              <h2 id="listas-publicas">Lists</h2>
            </div>
          </div>
          {perfil.listas_publicas.length ? (
            <ol className={styles.listaColecoes}>
              {perfil.listas_publicas.map((lista) => (
                <li key={lista.id}>
                  <Link href={"/listas/" + lista.id} className={styles.capaColecao} aria-label={"Open list " + lista.titulo}>
                    <VitrineLista listaId={lista.id} titulo={lista.titulo} compacta />
                  </Link>
                  <div className={styles.listaTexto}>
                    <h3><Link href={"/listas/" + lista.id}>{lista.titulo}</Link></h3>
                    
                  </div>
                  <Link href={"/listas/" + lista.id} aria-label={"Open " + lista.titulo} className={styles.seta}>↗</Link>
                </li>
              ))}
            </ol>
          ) : <p className={styles.vazio}>No public lists.</p>}
        </aside>
      </div>
    </>
  );
}

export default function PerfilPage({ params }: { params: ParametrosPerfil }) {
  return (
    <main className={styles.container}>
      <div className={styles.interior}>
        <nav className={styles.breadcrumb} aria-label="Navigation">
          <Link href="/">Discover</Link><span aria-hidden="true">/</span><span>Profile</span>
        </nav>
        <Suspense fallback={<p className={styles.vazio}>Loading profile…</p>}>
          <ConteudoPerfil params={params} />
        </Suspense>
      </div>
    </main>
  );
}
