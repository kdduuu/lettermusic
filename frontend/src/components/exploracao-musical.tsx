import Link from "next/link";
import { CapaAlbum } from "@/components/capa-album";
import { CapaArtista } from "@/components/capa-artista";
import { obterCapaAlbum } from "@/lib/catalogo";
import { FaixasInterativas } from "@/components/faixas-interativas";
import { BotaoAdicionarBusca } from "@/components/formularios-listas";
import { faixasAlbum, type Categoria, type Item } from "@/lib/exploracao";
import styles from "./exploracao-musical.module.css";
import { tipoMusicalEmPortugues } from "@/lib/visual-metadados";

export function ResultadosMusicais({
  itens, categoria, listaId, apresentacao = "lista", avaliacoes,
}: {
  itens: Item[];
  categoria: Categoria;
  listaId?: number;
  apresentacao?: "lista" | "galeria";
  avaliacoes?: Record<string, { media: number; quantidade: number }>;
}) {
  if (!itens.length) return <p className={styles.mensagem}>No results found.</p>;

  if (categoria === "albuns" && apresentacao === "galeria") {
    return (
      <ul className={styles.galeria}>
        {itens.map((item) => {
          const endereco = "/albuns/" + encodeURIComponent(item.id_musicbrainz);
          return (
            <li key={item.id_musicbrainz} className={styles.albumGaleria}>
              <Link href={endereco} className={styles.linkCapaGaleria} aria-label={"Open " + item.titulo}>
                <CapaAlbum
                  url={"https://coverartarchive.org/release-group/" + item.id_musicbrainz.toLowerCase() + "/front-500"}
                  titulo={item.titulo}
                  className={styles.capaGaleria}
                />
              </Link>
              <div className={styles.dadosGaleria}>
                <h3><Link href={endereco}>{item.titulo}</Link></h3>
                <p>{item.artista ?? "Unknown artist"}</p>
                <div className={styles.dadosLinha}>
                  <span>{[tipoMusicalEmPortugues(item.tipo), item.data?.slice(0, 4)].filter(Boolean).join(" · ")}</span>
                  {avaliacoes?.[item.id_musicbrainz] ? (
                    <strong className={styles.notaGaleria} title={
                      String(avaliacoes[item.id_musicbrainz].quantidade) +
                      " community ratings"
                    }>
                      ★ {avaliacoes[item.id_musicbrainz].media.toLocaleString("en-US", {
                        minimumFractionDigits: 1,
                        maximumFractionDigits: 1,
                      })}
                    </strong>
                  ) : null}
                </div>
              </div>
            </li>
          );
        })}
      </ul>
    );
  }

  return (
    <ul className={styles.resultados}>
      {itens.map((item) => (
        <li key={item.id_musicbrainz}>
          {categoria === "albuns" ? (
            <CapaAlbum
              key={item.id_musicbrainz}
              titulo={item.titulo}
              className={styles.capa}
              url={`https://coverartarchive.org/release-group/${item.id_musicbrainz.toLowerCase()}/front-500`}
            />
          ) : categoria === "artistas" ? (
            <CapaArtista nome={item.titulo} id={item.id_musicbrainz} />
          ) : <div className={styles.icone} aria-hidden="true">♪</div>}

          <div className={styles.info}>
            <h3>
              {categoria === "faixas" ? item.titulo : (
                <Link prefetch={false} href={`/${categoria}/${item.id_musicbrainz}`}>
                  {item.titulo}
                </Link>
              )}
            </h3>

            <p>{[item.artista, tipoMusicalEmPortugues(item.tipo), item.data?.slice(0, 4), item.subtitulo].filter(Boolean).join(" · ")}</p>

            {categoria === "albuns" && listaId ? (
              <BotaoAdicionarBusca id={item.id_musicbrainz} listaId={listaId} />
            ) : null}

            {categoria === "faixas" ? (
              <div className={styles.relacionados}>
                {item.relacionados.length ? (
                  <>
                    <p>Related releases</p>
                    {item.relacionados.map((r) => (
                      <Link prefetch={false} key={r.id_musicbrainz} href={`/albuns/${r.id_musicbrainz}`}>
                        {r.titulo}
                      </Link>
                    ))}
                  </>
                ) : (
                  <a href={`https://musicbrainz.org/recording/${item.id_musicbrainz}`} target="_blank" rel="noreferrer">
                    View recording on MusicBrainz
                  </a>
                )}
              </div>
            ) : null}
          </div>
        </li>
      ))}
    </ul>
  );
}

export function Paginacao({
  pagina, temProxima, endereco,
}: {
  pagina: number;
  temProxima: boolean;
  endereco: string;
}) {
  if (pagina === 1 && !temProxima) return null;
  const separador = endereco.includes("?") ? "&" : "?";

  return (
    <nav className={styles.paginacao} aria-label="Pagination">
      {pagina > 1 ? <Link prefetch={false} href={`${endereco}${separador}pagina=${pagina - 1}`}>Previous</Link> : null}
      <span>Page {pagina}</span>
      {temProxima && pagina < 1000 ? <Link prefetch={false} href={`${endereco}${separador}pagina=${pagina + 1}`}>Next</Link> : null}
    </nav>
  );
}

export async function FaixasDoAlbum({
  id, artista, album,
}: {
  id: string;
  artista: string;
  album: string;
}) {
  const [resultado, capa] = await Promise.all([faixasAlbum(id), obterCapaAlbum(id)]);
  return (
    <section className={styles.faixas} aria-label="Tracks">
      {!resultado.ok ? (
        <p role="alert" className={styles.mensagem}>{resultado.mensagem}</p>
      ) : !resultado.dados.faixas.length ? (
        <p className={styles.mensagem}>Tracks unavailable for this release.</p>
      ) : (
        <FaixasInterativas faixas={resultado.dados.faixas} capa={capa} artista={artista} album={album} />
      )}
    </section>
  );
}
