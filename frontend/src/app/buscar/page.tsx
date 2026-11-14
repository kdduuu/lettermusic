import { Suspense } from "react";
import { SearchForm } from "@/components/site-header";
import { pesquisarAlbuns } from "@/lib/catalogo";
import styles from "../page.module.css";

type ParametrosBusca = Promise<{
  termo?: string | string[];
}>;

async function ResultadosBusca({
  searchParams,
}: {
  searchParams: ParametrosBusca;
}) {
  const parametros = await searchParams;
  const termoBruto = Array.isArray(parametros.termo)
    ? parametros.termo[0] ?? ""
    : parametros.termo ?? "";
  const termo = termoBruto.trim();

  if (!termo) {
    return <p className={styles.message}>Informe um álbum para pesquisar.</p>;
  }

  if (termo.length < 2 || termo.length > 100) {
    return (
      <p className={styles.message} role="alert">
        A pesquisa deve ter entre 2 e 100 caracteres.
      </p>
    );
  }

  const resultado = await pesquisarAlbuns(termo);

  if (!resultado.ok) {
    return (
      <p className={styles.message} role="alert">
        {resultado.mensagem}
      </p>
    );
  }

  if (resultado.obras.length === 0) {
    return (
      <p className={styles.message}>
        Nenhum resultado encontrado para “{termo}”.
      </p>
    );
  }

  return (
    <section aria-label="Resultados da pesquisa" className={styles.results}>
      <h2>Resultados para “{termo}”</h2>
      <ul className={styles.resultList}>
        {resultado.obras.map((obra, index) => (
          <li
            className={styles.resultItem}
            key={obra.id_musicbrainz ?? `${obra.titulo ?? "obra"}-${index}`}
          >
            <div className={styles.coverFallback} aria-hidden="true">
              ♪
            </div>
            <div>
              <h3>{obra.titulo ?? "Título não informado"}</h3>
              <p>
                {obra.artista ?? "Artista não informado"}
                {obra.data_lancamento
                  ? ` · ${obra.data_lancamento.slice(0, 4)}`
                  : ""}
              </p>
            </div>
            <span className={styles.type}>{obra.tipo ?? "Obra"}</span>
          </li>
        ))}
      </ul>
    </section>
  );
}

export default function BuscarPage({
  searchParams,
}: {
  searchParams: ParametrosBusca;
}) {
  return (
    <main className={styles.container}>
      <section className={styles.searchPage}>
        <span className={styles.accent} aria-hidden="true" />
        <h1>Buscar álbuns</h1>
        <SearchForm variant="hero" />
        <Suspense
          fallback={<p className={styles.message}>Buscando álbuns...</p>}
        >
          <ResultadosBusca searchParams={searchParams} />
        </Suspense>
      </section>
    </main>
  );
}