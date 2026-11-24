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
  return nota.toLocaleString("pt-BR", { minimumFractionDigits: 1, maximumFractionDigits: 2 });
}

function formatarData(data: string) {
  const partes = /^(\d{4})-(\d{2})-(\d{2})/.exec(data);
  return partes ? `${partes[3]}/${partes[2]}/${partes[1]}` : "";
}

export async function DestaquesMusicais({ tipo }: { tipo: TipoDestaque }) {
  const resultado = await consultarDestaques(tipo);
  if (!resultado.ok) return <p role="alert" className={styles.mensagem}>{resultado.mensagem}</p>;
  if (!resultado.dados.length) return <p className={styles.mensagem}>Os destaques aparecerão conforme a comunidade registrar suas atividades.</p>;
  const capas = await consultarCapas(resultado.dados);
  return (
    <ul className={styles.grade}>
      {resultado.dados.map((obra) => (
        <li key={obra.obra_id}>
          <Link href={`/albuns/${encodeURIComponent(obra.id_musicbrainz)}`} className={styles.album}>
            <CapaAlbum url={capas.get(obra.id_musicbrainz) ?? null} titulo={obra.titulo} className={styles.capaDestaque} />
            <strong>{obra.titulo}</strong>
          </Link>
          <p>{obra.artista ?? "Artista não informado"}</p>
          <p>{tipo === "mais-ouvidas" ? `${obra.total_escutas} ${obra.total_escutas === 1 ? "escuta" : "escutas"}` : obra.media !== undefined ? `${formatarNota(obra.media)}/5 · ${obra.quantidade_avaliacoes} ${obra.quantidade_avaliacoes === 1 ? "avaliação" : "avaliações"}` : ""}</p>
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
  if (!reviews.length) return <p className={styles.mensagem}>Nenhuma review publicada nesta página.</p>;
  const capas = await consultarCapas(reviews);
  return (
    <ul className={apresentacao === "editorial" ? styles.reviews + " " + styles.reviewsPagina : styles.reviews}>
      {reviews.map((review) => (
        <li key={review.id} className={styles.review}>
          <Link href={`/albuns/${encodeURIComponent(review.id_musicbrainz)}`} aria-label={`Abrir álbum ${review.titulo}`}>
            <CapaAlbum url={capas.get(review.id_musicbrainz) ?? null} titulo={review.titulo} className={styles.capaReview} />
          </Link>
          <article>
            <h3><Link href={`/albuns/${encodeURIComponent(review.id_musicbrainz)}`}>{review.titulo}</Link></h3>
            <p className={styles.artista}>{review.artista ?? "Artista não informado"}</p>
            <p className={styles.meta}>
              <Link href={`/usuarios/${encodeURIComponent(review.username)}`}>{review.nome_exibicao} (@{review.username})</Link>
              {" · "}<time dateTime={review.criada_em}>{formatarData(review.criada_em)}</time>
              {review.nota !== null ? <span> · ★ {formatarNota(review.nota)}/5</span> : null}
              {review.atualizada_em ? <span> · Editada</span> : null}
            </p>
            <p className={resumo ? styles.resumo : styles.texto}>{review.texto}</p>
            {!resumo ? <Link className={styles.verAlbum} href={"/albuns/" + encodeURIComponent(review.id_musicbrainz)}>Abrir álbum ↗</Link> : null}
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
  if (!resultado.dados.length) return <p className={styles.mensagem}>As médias aparecerão quando houver avaliações públicas.</p>;
  return (
    <ol className={styles.rankingAvaliacoes}>
      {resultado.dados.map((obra, indice) => (
        <li key={obra.obra_id}>
          <span className={styles.posicaoRanking}>{String(indice + 1).padStart(2, "0")}</span>
          <div className={styles.albumRanking}>
            <Link href={"/albuns/" + encodeURIComponent(obra.id_musicbrainz)}>{obra.titulo}</Link>
            <p>{obra.artista ?? "Artista não informado"} · {obra.quantidade_avaliacoes} {obra.quantidade_avaliacoes === 1 ? "avaliação" : "avaliações"}</p>
          </div>
          <strong className={styles.notaRanking}>★ {formatarNota(obra.media ?? 0)}</strong>
        </li>
      ))}
    </ol>
  );
}
