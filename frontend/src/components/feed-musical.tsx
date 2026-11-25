import Link from "next/link";
import { CapaAlbum } from "@/components/capa-album";
import { obterCapaAlbum } from "@/lib/catalogo";
import { consultarDestaques, consultarFeedReviews, type ReviewFeed, type TipoDestaque } from "@/lib/feed";
import styles from "./feed-musical.module.css";

async function consultarCapas(itens: { id_musicbrainz: string }[]) {
  const ids = Array.from(new Set(itens.map((item) => item.id_musicbrainz)));
  return new Map(await Promise.all(ids.map(async (id) => [id, await obterCapaAlbum(id)] as const)));
}

function formatarNota(nota: number) {
  return nota.toLocaleString("en-US", { minimumFractionDigits: 1, maximumFractionDigits: 2 });
}

function formatarData(data: string) {
  const partes = /^(\d{4})-(\d{2})-(\d{2})/.exec(data);
  return partes ? `${partes[3]}/${partes[2]}/${partes[1]}` : "";
}

export async function DestaquesMusicais({ tipo }: { tipo: TipoDestaque }) {
  const [resultado, avaliacoes] = await Promise.all([
    consultarDestaques(tipo),
    tipo === "mais-ouvidas" ? consultarDestaques("melhor-avaliadas") : Promise.resolve(null),
  ]);
  if (!resultado.ok) return <p role="alert" className={styles.mensagem}>{resultado.mensagem}</p>;
  if (!resultado.dados.length) return <p className={styles.mensagem}>No activity yet.</p>;
  const capas = await consultarCapas(resultado.dados);
  const notas = new Map(avaliacoes?.ok
    ? avaliacoes.dados.map((obra) => [obra.id_musicbrainz, obra.media] as const)
    : []);
  return (
    <ul className={styles.grade} data-count={Math.min(resultado.dados.length, 4)}>
      {resultado.dados.map((obra) => (
        <li key={obra.obra_id}>
          <Link href={`/albuns/${encodeURIComponent(obra.id_musicbrainz)}`} className={styles.album}>
            <CapaAlbum url={capas.get(obra.id_musicbrainz) ?? null} titulo={obra.titulo} className={styles.capaDestaque} />
            <strong>{obra.titulo}</strong>
          </Link>
          <p>{obra.artista ?? "Unknown artist"}</p>
          <div className={styles.dadosScore}>
            {notas.get(obra.id_musicbrainz) !== undefined || obra.media !== undefined ? (
              <strong className={styles.scoreAlbum}>★ {formatarNota(notas.get(obra.id_musicbrainz) ?? obra.media ?? 0)}</strong>
            ) : null}
            {tipo === "mais-ouvidas" && obra.total_escutas !== undefined ? (
              <span>{obra.total_escutas} {obra.total_escutas === 1 ? "play" : "plays"}</span>
            ) : null}
          </div>
        </li>
      ))}
    </ul>
  );
}

export async function CardsReviews({
  reviews, resumo = false, apresentacao = "resumo",
}: {
  reviews: ReviewFeed[];
  resumo?: boolean;
  apresentacao?: "resumo" | "editorial";
}) {
  if (!reviews.length) return <p className={styles.mensagem}>No reviews yet.</p>;
  const capas = await consultarCapas(reviews);
  return (
    <ul className={apresentacao === "editorial" ? styles.reviews + " " + styles.reviewsPagina : styles.reviews}>
      {reviews.map((review) => (
        <li key={review.id} className={styles.review}>
          <Link href={`/albuns/${encodeURIComponent(review.id_musicbrainz)}`} aria-label={`Open album ${review.titulo}`}>
            <CapaAlbum url={capas.get(review.id_musicbrainz) ?? null} titulo={review.titulo} className={styles.capaReview} />
          </Link>
          <article className={styles.reviewConteudo}>
            <div className={styles.reviewTituloLinha}>
              <h3><Link href={`/albuns/${encodeURIComponent(review.id_musicbrainz)}`}>{review.titulo}</Link></h3>
              {review.nota !== null ? (
                <strong className={styles.reviewNota} aria-label={`Rating ${formatarNota(review.nota)} out of 5`}>
                  ★ {formatarNota(review.nota)}
                </strong>
              ) : null}
            </div>
            <p className={styles.artista}>{review.artista ?? "Unknown artist"}</p>
            <p className={styles.meta}>
              {apresentacao === "editorial" ? (
                <span className={styles.autorMarca} aria-hidden="true">
                  {Array.from(review.nome_exibicao.trim())[0]?.toLocaleUpperCase("en-US") || "♪"}
                </span>
              ) : null}
              <Link href={`/usuarios/${encodeURIComponent(review.username)}`}>{review.nome_exibicao}</Link>
              <span aria-hidden="true">·</span>
              <time dateTime={review.criada_em}>{formatarData(review.criada_em)}</time>
            </p>
            <p className={resumo ? styles.resumo : styles.texto}>{review.texto}</p>
          </article>
        </li>
      ))}
    </ul>
  );
}

export async function ReviewsRecentes() {
  const resultado = await consultarFeedReviews(1, 3);
  if (!resultado.ok) return <p role="alert" className={styles.mensagem}>{resultado.mensagem}</p>;
  return <CardsReviews reviews={resultado.dados.resultados} resumo />;
}
export async function ResumoBemAvaliados() {
  const resultado = await consultarDestaques("melhor-avaliadas");
  if (!resultado.ok) return <p role="alert" className={styles.mensagem}>{resultado.mensagem}</p>;
  if (!resultado.dados.length) return <p className={styles.mensagem}>No public ratings yet.</p>;
  return (
    <ul className={styles.rankingAvaliacoes}>
      {resultado.dados.map((obra) => (
        <li key={obra.obra_id}>
          
          <div className={styles.albumRanking}>
            <Link href={"/albuns/" + encodeURIComponent(obra.id_musicbrainz)}>{obra.titulo}</Link>
            <p>{obra.artista ?? "Unknown artist"}</p>
          </div>
          <strong className={styles.notaRanking}>★ {formatarNota(obra.media ?? 0)}</strong>
        </li>
      ))}
    </ul>
  );
}
