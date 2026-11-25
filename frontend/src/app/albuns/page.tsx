import Link from "next/link";
import { Suspense } from "react";
import { Paginacao, ResultadosMusicais } from "@/components/exploracao-musical";
import { catalogoLocal, obterPagina } from "@/lib/exploracao";
import { consultarDestaques } from "@/lib/feed";
import styles from "../page.module.css";
import controles from "@/components/controles.module.css";

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
  const [resultado, notas] = await Promise.all([
    catalogoLocal(termo, tipo, pagina),
    consultarDestaques("melhor-avaliadas"),
  ]);
  const avaliacoes = Object.fromEntries(
    notas.ok ? notas.dados
      .filter((obra) => obra.media !== undefined && obra.quantidade_avaliacoes !== undefined)
      .map((obra) => [
        obra.id_musicbrainz,
        { media: obra.media as number, quantidade: obra.quantidade_avaliacoes as number },
      ]) : []
  );
  const p = new URLSearchParams({ termo, tipo });

  return (
    <>
      <form action="/albuns" className={controles.formulario}>
        <label htmlFor="termo-catalogo" className={styles.visuallyHidden}>Search albums</label>
        <div className={controles.linha + " " + controles.catalogo}>
          <input className={controles.campo} id="termo-catalogo" name="termo" type="search" maxLength={100} defaultValue={termo} placeholder="Title or artist" />
          <label htmlFor="tipo-catalogo" className={styles.visuallyHidden}>Release type</label>
          <select className={controles.selecao} id="tipo-catalogo" name="tipo" defaultValue={tipo}>
            <option value="todos">All</option>
            <option value="Album">Albums</option>
            <option value="Single">Singles</option>
            <option value="EP">EPs</option>
          </select>
          <button className={controles.primario} type="submit">Filter</button>
        </div>
      </form>

      <section className={styles.results}>
        {resultado.ok ? (
          <>
            <div className={styles.catalogoResultados}>
              <ResultadosMusicais itens={resultado.dados.resultados} categoria="albuns" apresentacao="galeria" avaliacoes={avaliacoes} />
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
        
        <h1>Albums</h1>
        
        <Link href="/buscar" className={styles.linkExternoCatalogo}>Search full catalog</Link>
      </section>
      <Suspense fallback={<p className={styles.message}>Loading catalog…</p>}>
        <Conteudo searchParams={searchParams} />
      </Suspense>
    </main>
  );
}
