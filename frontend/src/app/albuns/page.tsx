import Link from "next/link";
import { Suspense } from "react";
import { Paginacao, ResultadosMusicais } from "@/components/exploracao-musical";
import { catalogoLocal, obterPagina } from "@/lib/exploracao";
import styles from "../page.module.css";

type Parametros = Promise<{
  termo?: string | string[];
  tipo?: string | string[];
  pagina?: string | string[];
}>;

async function Conteudo({ searchParams }: { searchParams: Parametros }) {
  const params = await searchParams;
  const termo = typeof params.termo === "string" ? params.termo.trim().slice(0, 100) : "";
  const tipo = ["Album", "Single", "EP"].includes(String(params.tipo)) ? String(params.tipo) : "todos";
  const pagina = obterPagina(params.pagina);
  const resultado = await catalogoLocal(termo, tipo, pagina);
  const p = new URLSearchParams({ termo, tipo });

  return (
    <>
      <form action="/albuns" className={styles.buscaLista}>
        <label htmlFor="termo-catalogo" className={styles.visuallyHidden}>Pesquisar álbuns</label>
        <div>
          <input id="termo-catalogo" name="termo" type="search" maxLength={100} defaultValue={termo} placeholder="Título ou artista" />
          <button type="submit">Filtrar</button>
        </div>
        <div className={styles.filtroCatalogo}>
          <label htmlFor="tipo-catalogo">Tipo</label>
          <select id="tipo-catalogo" name="tipo" defaultValue={tipo}>
            <option value="todos">Todos</option>
            <option value="Album">Álbuns</option>
            <option value="Single">Singles</option>
            <option value="EP">EPs</option>
          </select>
        </div>
      </form>

      <section className={styles.results}>
        {resultado.ok ? (
          <>
            <div className={styles.catalogoResultados}>
              <ResultadosMusicais itens={resultado.dados.resultados} categoria="albuns" apresentacao="galeria" />
            </div>
            <Paginacao pagina={pagina} temProxima={resultado.dados.tem_proxima} endereco={`/albuns?${p}`} />
          </>
        ) : <p role="alert" className={styles.message}>{resultado.mensagem}</p>}
      </section>
    </>
  );
}

export default function AlbunsPage({ searchParams }: { searchParams: Parametros }) {
  return (
    <main className={styles.container}>
      <section className={styles.hero + " " + styles.catalogoHero}>
        
        <h1>Álbuns</h1>
        
        <Link href="/buscar" className={styles.linkExternoCatalogo}>MusicBrainz ↗</Link>
      </section>
      <Suspense fallback={<p className={styles.message}>Carregando catálogo...</p>}>
        <Conteudo searchParams={searchParams} />
      </Suspense>
    </main>
  );
}
