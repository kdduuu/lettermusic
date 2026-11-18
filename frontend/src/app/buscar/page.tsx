import Link from "next/link";
import { Suspense } from "react";
import { SearchForm } from "@/components/site-header";
import { BotaoAdicionarBusca } from "@/components/formularios-listas";
import { pesquisarAlbuns } from "@/lib/catalogo";
import { idPositivo, verificarMinhaLista } from "@/lib/listas";
import { obterTokenSessao } from "@/lib/sessao";
import styles from "../page.module.css";

type ParametrosBusca = Promise<{ termo?: string | string[]; lista?: string | string[] }>;

async function ResultadosBusca({ searchParams }: { searchParams: ParametrosBusca }) {
  const parametros = await searchParams;
  const termoBruto = Array.isArray(parametros.termo)
    ? parametros.termo[0] ?? ""
    : parametros.termo ?? "";
  const termo = termoBruto.trim();
  const rawId = Array.isArray(parametros.lista) ? parametros.lista[0] : parametros.lista;
  const listaId = idPositivo(rawId);

  if (!termo) {
    return <p className={styles.message}>Informe um álbum para pesquisar.</p>;
  }
  if (termo.length < 2 || termo.length > 100) {
    return <p className={styles.message} role="alert">A pesquisa deve ter entre 2 e 100 caracteres.</p>;
  }

  // Exibe o botao de adicao somente apos a API confirmar a propriedade da lista.
  const token = listaId ? await obterTokenSessao() : null;
  const minhaLista = listaId && token ? await verificarMinhaLista(listaId, token) : null;
  const listaPermitida = minhaLista?.ok ? minhaLista.dados : null;

  const resultado = await pesquisarAlbuns(termo);
  if (!resultado.ok) return <p className={styles.message} role="alert">{resultado.mensagem}</p>;
  if (resultado.obras.length === 0) return <p className={styles.message}>Nenhum resultado encontrado para “{termo}”.</p>;

  return (
    <section aria-label="Resultados da pesquisa" className={styles.results}>
      <h2>Resultados para “{termo}”</h2>
      {listaId && !listaPermitida ? (
        <p className={styles.message} role="alert">Você precisa ser proprietário da lista para adicionar álbuns.</p>
      ) : null}
      {listaPermitida ? (
        <p className={styles.message}>Adicionando à lista <Link href={`/listas/${listaPermitida.id}`}>{listaPermitida.titulo}</Link>.</p>
      ) : null}
      <ul className={styles.resultList}>
        {resultado.obras.map((obra, index) => (
          <li className={styles.resultItem} key={obra.id_musicbrainz ?? `${obra.titulo ?? "obra"}-${index}`}>
            <div className={styles.coverFallback} aria-hidden="true">♪</div>
            <div>
              {obra.id_musicbrainz ? (
                <h3>
                  <Link className={styles.resultLink} href={`/albuns/${encodeURIComponent(obra.id_musicbrainz)}`}>
                    {obra.titulo ?? "Título não informado"}
                  </Link>
                </h3>
              ) : <h3>{obra.titulo ?? "Título não informado"}</h3>}
              <p>
                {obra.artista ?? "Artista não informado"}
                {obra.data_lancamento ? ` · ${obra.data_lancamento.slice(0, 4)}` : ""}
              </p>
              {listaPermitida && obra.id_musicbrainz ? (
                <BotaoAdicionarBusca id={obra.id_musicbrainz} listaId={listaPermitida.id} />
              ) : null}
            </div>
            <span className={styles.type}>{obra.tipo ?? "Obra"}</span>
          </li>
        ))}
      </ul>
    </section>
  );
}

export default function BuscarPage({ searchParams }: { searchParams: ParametrosBusca }) {
  return (
    <main className={styles.container}>
      <section className={styles.searchPage}>
        <span className={styles.accent} aria-hidden="true" />
        <h1>Buscar álbuns</h1>
        <Suspense fallback={<p className={styles.message}>Carregando pesquisa...</p>}>
          <BuscadorDaLista searchParams={searchParams} />
        </Suspense>
        <Suspense fallback={<p className={styles.message}>Buscando álbuns...</p>}>
          <ResultadosBusca searchParams={searchParams} />
        </Suspense>
      </section>
    </main>
  );
}

async function BuscadorDaLista({ searchParams }: { searchParams: ParametrosBusca }) {
  const parametros = await searchParams;
  const rawId = Array.isArray(parametros.lista) ? parametros.lista[0] : parametros.lista;
  const id = idPositivo(rawId);
  if (!id) return <SearchForm variant="hero" />;
  return (
    <form role="search" action="/buscar" method="get" className={styles.buscaLista}>
      <input type="hidden" name="lista" value={id} />
      <label htmlFor="termo-lista">Buscar outro álbum para a lista</label>
      <div>
        <input id="termo-lista" type="search" name="termo" minLength={2} maxLength={100} required placeholder="Buscar álbuns..." />
        <button type="submit">Buscar</button>
      </div>
    </form>
  );
}