import Link from "next/link";
import { notFound } from "next/navigation";
import { Suspense } from "react";
import { CapaAlbum } from "@/components/capa-album";
import { obterCapaAlbum } from "@/lib/catalogo";
import { consultarPerfilPublico, type AlbumRecente } from "@/lib/perfis";
import styles from "./page.module.css";

type ParametrosPerfil = Promise<{ username: string }>;

function anoCadastro(data: string): string {
  const ano = Number(data.slice(0, 4));
  return ano >= 2000 && ano <= 2100 ? String(ano) : "";
}
function dataResumida(data: string): string {
  const partes = /^(\d{4})-(\d{2})-(\d{2})/.exec(data);
  return partes ? partes[3] + "/" + partes[2] + "/" + partes[1] : "";
}

async function CapasRecentes({ albuns }: { albuns: AlbumRecente[] }) {
  const urls = await Promise.all(albuns.map((album) => obterCapaAlbum(album.id_musicbrainz)));
  return (
    <div className={styles.gradeCapas}>
      {albuns.map((album, indice) => (
        <Link
          key={album.id_musicbrainz}
          href={"/albuns/" + encodeURIComponent(album.id_musicbrainz)}
          className={styles.itemCapa}
          title={album.titulo + " — " + (album.artista ?? "Artista não informado")}
        >
          <CapaAlbum url={urls[indice]} titulo={album.titulo} className={styles.capa} />
          <span className={styles.nomeAlbum}>{album.titulo}</span>
          <span className={styles.artistaAlbum}>{album.artista ?? "Artista não informado"}</span>
        </Link>
      ))}
    </div>
  );
}

async function ConteudoPerfil({ params }: { params: ParametrosPerfil }) {
  const { username } = await params;
  const resultado = await consultarPerfilPublico(username);
  if (!resultado.ok) {
    if (resultado.status === 404) notFound();
    return <p role="alert" className={styles.erro}>{resultado.mensagem}</p>;
  }
  const { perfil } = resultado;
  const inicial = Array.from(perfil.nome_exibicao.trim()).slice(0, 1).join("").toLocaleUpperCase("pt-BR") || "♪";
  const ano = anoCadastro(perfil.criado_em);

  return (
    <>
      <header className={styles.perfilHero}>
        <div className={styles.identidade}>
          <div className={styles.avatar} aria-label={"Inicial de " + perfil.nome_exibicao} role="img">{inicial}</div>
          <div className={styles.informacoes}>
            <p className={styles.sobretitulo}>Arquivo musical pessoal {ano ? " · Desde " + ano : ""}</p>
            <h1>{perfil.nome_exibicao}</h1>
            <p className={styles.username}>@{perfil.username}</p>
            {perfil.bio ? <p className={styles.bio}>{perfil.bio}</p> : null}
          </div>
        </div>
        <dl className={styles.estatisticas} aria-label="Atividade pública do perfil">
          <div><dd>{perfil.estatisticas.avaliacoes}</dd><dt>Avaliações</dt></div>
          <div><dd>{perfil.estatisticas.reviews}</dd><dt>Reviews</dt></div>
          <div><dd>{perfil.estatisticas.listas_publicas}</dd><dt>Listas públicas</dt></div>
        </dl>
      </header>

      <section className={styles.discografia} aria-labelledby="albuns-recentes">
        <div className={styles.tituloSecao}>
          <div>
            <p className={styles.sobretitulo}>Atividade musical recente</p>
            <h2 id="albuns-recentes">A música fala por si.</h2>
          </div>
          <p className={styles.nota}>Até cinco álbuns das avaliações e reviews recentes.</p>
        </div>
        {perfil.albuns_recentes.length ? (
          <Suspense fallback={<p className={styles.vazio}>Carregando capas...</p>}>
            <CapasRecentes albuns={perfil.albuns_recentes} />
          </Suspense>
        ) : <p className={styles.vazio}>Ainda não há avaliações ou reviews públicas com álbuns para mostrar.</p>}
      </section>

      <div className={styles.corpoEditorial}>
        <section className={styles.reviews} aria-labelledby="reviews-recentes">
          <div className={styles.tituloSecao}>
            <div>
              <p className={styles.sobretitulo}>Diário de escuta</p>
              <h2 id="reviews-recentes">Palavras sobre música</h2>
            </div>
          </div>
          {perfil.reviews_recentes.length ? (
            <ul className={styles.feed}>
              {perfil.reviews_recentes.map((review) => (
                <li key={review.id}>
                  <div className={styles.reviewTopo}>
                    <Link href={"/albuns/" + encodeURIComponent(review.id_musicbrainz)} className={styles.reviewAlbum}>{review.titulo}</Link>
                    <time dateTime={review.criada_em}>{dataResumida(review.criada_em)}</time>
                  </div>
                  <p className={styles.reviewArtista}>{review.artista ?? "Artista não informado"}</p>
                  <p className={styles.reviewTexto}>{review.texto}</p>
                  <Link href={"/albuns/" + encodeURIComponent(review.id_musicbrainz)} className={styles.reviewLink}>Ver álbum <span aria-hidden="true">↗</span></Link>
                </li>
              ))}
            </ul>
          ) : <p className={styles.vazio}>Ainda não há reviews públicas.</p>}
        </section>

        <aside className={styles.listas} aria-labelledby="listas-publicas">
          <div className={styles.tituloSecao}>
            <div>
              <p className={styles.sobretitulo}>Coleções pessoais</p>
              <h2 id="listas-publicas">Listas criadas</h2>
            </div>
          </div>
          {perfil.listas_publicas.length ? (
            <ol className={styles.listaColecoes}>
              {perfil.listas_publicas.map((lista, indice) => (
                <li key={lista.id}>
                  <span className={styles.indice}>{String(indice + 1).padStart(2, "0")}</span>
                  <div className={styles.listaTexto}>
                    <h3><Link href={"/listas/" + lista.id}>{lista.titulo}</Link></h3>
                    {lista.descricao ? <p>{lista.descricao}</p> : <p>Uma seleção musical pessoal.</p>}
                  </div>
                  <Link href={"/listas/" + lista.id} aria-label={"Abrir " + lista.titulo} className={styles.seta}>↗</Link>
                </li>
              ))}
            </ol>
          ) : <p className={styles.vazio}>Nenhuma lista pública criada por enquanto.</p>}
        </aside>
      </div>
    </>
  );
}

export default function PerfilPage({ params }: { params: ParametrosPerfil }) {
  return (
    <main className={styles.container}>
      <div className={styles.interior}>
        <nav className={styles.breadcrumb} aria-label="Navegação">
          <Link href="/">Descobrir</Link><span aria-hidden="true">/</span><span>Perfil</span>
        </nav>
        <Suspense fallback={<p className={styles.vazio}>Carregando perfil...</p>}>
          <ConteudoPerfil params={params} />
        </Suspense>
      </div>
    </main>
  );
}
