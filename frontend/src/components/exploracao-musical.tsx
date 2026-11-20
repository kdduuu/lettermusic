import Link from "next/link";
import { CapaAlbum } from "@/components/capa-album";
import { BotaoAdicionarBusca } from "@/components/formularios-listas";
import { faixasAlbum, type Categoria, type Item } from "@/lib/exploracao";
import styles from "./exploracao-musical.module.css";

export function ResultadosMusicais({
  itens, categoria, listaId,
}: {
  itens: Item[];
  categoria: Categoria;
  listaId?: number;
}) {
  if (!itens.length) return <p className={styles.mensagem}>Nenhum resultado encontrado.</p>;

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
          ) : <div className={styles.icone} aria-hidden="true">{categoria === "artistas" ? "◎" : "♪"}</div>}

          <div className={styles.info}>
            <h3>
              {categoria === "faixas" ? item.titulo : (
                <Link prefetch={false} href={`/${categoria}/${item.id_musicbrainz}`}>
                  {item.titulo}
                </Link>
              )}
            </h3>

            <p>{[item.artista, item.tipo, item.data?.slice(0, 4), item.subtitulo].filter(Boolean).join(" · ")}</p>

            {categoria === "albuns" && listaId ? (
              <BotaoAdicionarBusca id={item.id_musicbrainz} listaId={listaId} />
            ) : null}

            {categoria === "faixas" ? (
              <div className={styles.relacionados}>
                {item.relacionados.length ? (
                  <>
                    <p>Lançamentos associados</p>
                    {item.relacionados.map((r) => (
                      <Link prefetch={false} key={r.id_musicbrainz} href={`/albuns/${r.id_musicbrainz}`}>
                        {r.titulo}
                      </Link>
                    ))}
                  </>
                ) : (
                  <a href={`https://musicbrainz.org/recording/${item.id_musicbrainz}`} target="_blank" rel="noreferrer">
                    Consultar gravação no MusicBrainz
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
  const separador = endereco.includes("?") ? "&" : "?";

  return (
    <nav className={styles.paginacao} aria-label="Paginação">
      {pagina > 1 ? <Link prefetch={false} href={`${endereco}${separador}pagina=${pagina - 1}`}>Anterior</Link> : null}
      <span>Página {pagina}</span>
      {temProxima && pagina < 1000 ? <Link prefetch={false} href={`${endereco}${separador}pagina=${pagina + 1}`}>Próxima</Link> : null}
    </nav>
  );
}

function duracao(ms: number | null) {
  if (ms === null) return "—";
  const segundos = Math.floor(ms / 1000);
  return `${Math.floor(segundos / 60)}:${String(segundos % 60).padStart(2, "0")}`;
}

export async function FaixasDoAlbum({ id }: { id: string }) {
  const resultado = await faixasAlbum(id);

  return (
    <section className={styles.faixas}>
      <h2>Faixas</h2>
      {!resultado.ok ? (
        <p role="alert" className={styles.mensagem}>{resultado.mensagem}</p>
      ) : !resultado.dados.faixas.length ? (
        <p className={styles.mensagem}>Nenhuma faixa disponível para a edição consultada.</p>
      ) : (
        <>
          <p className={styles.mensagem}>
            Edição consultada: {resultado.dados.edicao}
            {resultado.dados.data ? ` · ${resultado.dados.data}` : ""}
            {resultado.dados.pais ? ` · ${resultado.dados.pais}` : ""}
          </p>
          <ul>
            {resultado.dados.faixas.map((faixa, indice) => (
              <li key={indice}>
                <span>{faixa.disco > 1 ? `${faixa.disco}.` : ""}{faixa.numero}</span>
                <strong>{faixa.titulo}</strong>
                <span>{duracao(faixa.duracao_ms)}</span>
              </li>
            ))}
          </ul>
        </>
      )}
    </section>
  );
}
