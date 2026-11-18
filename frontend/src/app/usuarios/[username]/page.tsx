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

async function CapasPublicas({ albuns }: { albuns: AlbumRecente[] }) {
  const urls = await Promise.all(albuns.map((album) => obterCapaAlbum(album.id_musicbrainz)));
  return (
    <div className={styles.gradeCapas}>
      {albuns.map((album, indice) => (
        <Link
          key={album.id_musicbrainz}
          className={styles.itemCapa}
          href={`/albuns/${encodeURIComponent(album.id_musicbrainz)}`}
          title={`${album.titulo} — ${album.artista ?? "Artista não informado"}`}
        >
          <CapaAlbum url={urls[indice]} titulo={album.titulo} className={styles.capa} />
          <span>{album.titulo}</span>
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
  const iniciais = Array.from(perfil.nome_exibicao.trim()).slice(0, 1).join("").toLocaleUpperCase("pt-BR") || "♪";
  const ano = anoCadastro(perfil.criado_em);
  return (
    <>
      <section className={styles.cabecalho} aria-label="Apresentação do perfil">
        <div className={styles.avatar} aria-hidden="true">{iniciais}</div>
        <div className={styles.apresentacao}>
          <p className={styles.etiqueta}>Perfil musical</p>
          <h1>{perfil.nome_exibicao}</h1>
          <p className={styles.username}>@{perfil.username}{ano ? ` · Desde ${ano}` : ""}</p>
          {perfil.bio ? <p className={styles.bio}>{perfil.bio}</p> : null}
        </div>
      </section>

      <dl className={styles.estatisticas} aria-label="Estatísticas públicas">
        <div><dt>Avaliações</dt><dd>{perfil.estatisticas.avaliacoes}</dd></div>
        <div><dt>Reviews</dt><dd>{perfil.estatisticas.reviews}</dd></div>
        <div><dt>Listas públicas</dt><dd>{perfil.estatisticas.listas_publicas}</dd></div>
      </dl>

      <section className={styles.secao} aria-labelledby="titulo-albuns">
        <div className={styles.tituloSecao}>
          <h2 id="titulo-albuns">Álbuns recentes</h2>
          <span>Até 5 avaliações e reviews públicas</span>
        </div>
        {perfil.albuns_recentes.length ? (
          <Suspense fallback={<p className={styles.vazio}>Carregando capas...</p>}>
            <CapasPublicas albuns={perfil.albuns_recentes} />
          </Suspense>
        ) : <p className={styles.vazio}>Este perfil ainda não tem álbuns avaliados ou resenhados.</p>}
      </section>

      <section className={styles.secao} aria-labelledby="titulo-reviews">
        <div className={styles.tituloSecao}><h2 id="titulo-reviews">Reviews recentes</h2></div>
        {perfil.reviews_recentes.length ? (
          <ul className={styles.feed}>
            {perfil.reviews_recentes.map((review) => (
              <li key={review.id}>
                <div className={styles.tituloReview}>
                  <Link href={`/albuns/${encodeURIComponent(review.id_musicbrainz)}`}>{review.titulo}</Link>
                  <span>{review.artista ?? "Artista não informado"}</span>
                </div>
                <p>{review.texto}</p>
              </li>
            ))}
          </ul>
        ) : <p className={styles.vazio}>Nenhuma review pública por enquanto.</p>}
      </section>

      <section className={styles.secao} aria-labelledby="titulo-listas">
        <div className={styles.tituloSecao}><h2 id="titulo-listas">Listas públicas</h2></div>
        {perfil.listas_publicas.length ? (
          <ul className={styles.listas}>
            {perfil.listas_publicas.map((lista) => (
              <li key={lista.id}>
                <h3><Link href={`/listas/${lista.id}`}>{lista.titulo}</Link></h3>
                {lista.descricao ? <p>{lista.descricao}</p> : null}
              </li>
            ))}
          </ul>
        ) : <p className={styles.vazio}>Nenhuma lista pública criada ainda.</p>}
      </section>
    </>
  );
}

export default function PerfilPage({ params }: { params: ParametrosPerfil }) {
  return (
    <main className={styles.container}>
      <Link href="/" className={styles.voltar}>Descobrir</Link>
      <Suspense fallback={<p className={styles.vazio}>Carregando perfil...</p>}>
        <ConteudoPerfil params={params} />
      </Suspense>
    </main>
  );
}