import Link from "next/link";
import { Suspense } from "react";
import { Paginacao, ResultadosMusicais } from "@/components/exploracao-musical";
import { buscar, obterPagina, type Categoria } from "@/lib/exploracao";
import { idPositivo, verificarMinhaLista } from "@/lib/listas";
import { obterTokenSessao } from "@/lib/sessao";
import styles from "../page.module.css";

type Parametros = Promise<{
  termo?: string | string[];
  categoria?: string | string[];
  pagina?: string | string[];
  lista?: string | string[];
}>;

const CATEGORIAS: Categoria[] = ["albuns", "artistas", "faixas"];
const TITULOS = { albuns: "Álbuns", artistas: "Artistas", faixas: "Faixas" };

async function Conteudo({ searchParams }: { searchParams: Parametros }) {
  const params = await searchParams;
  const termo = typeof params.termo === "string" ? params.termo.trim() : "";
  const listaId = idPositivo(typeof params.lista === "string" ? params.lista : undefined);
  const categoria = !listaId && CATEGORIAS.includes(params.categoria as Categoria)
    ? params.categoria as Categoria : listaId ? "albuns" : "todos";

  const pagina = obterPagina(params.pagina);
  const token = listaId ? await obterTokenSessao() : null;
  const minhaLista = listaId && token ? await verificarMinhaLista(listaId, token) : null;
  const permitida = minhaLista?.ok ? minhaLista.dados : null;

  function endereco(tipo: string) {
    const p = new URLSearchParams({ termo, categoria: tipo });
    if (listaId) p.set("lista", String(listaId));
    return `/buscar?${p}`;
  }

  return (
    <>
      <form action="/buscar" className={styles.buscaLista} role="search">
        <label htmlFor="busca-exploracao">Pesquisar música</label>
        {listaId ? <input type="hidden" name="lista" value={listaId} /> : null}
        {categoria !== "todos" ? <input type="hidden" name="categoria" value={categoria} /> : null}
        <div>
          <input id="busca-exploracao" name="termo" type="search" defaultValue={termo} required minLength={2} maxLength={100} placeholder="Álbum, artista ou faixa..." />
          <button type="submit">Buscar</button>
        </div>
      </form>

      {permitida ? (
        <p className={styles.message}>Adicionando à lista <Link href={`/listas/${permitida.id}`}>{permitida.titulo}</Link>.</p>
      ) : listaId ? (
        <p className={styles.message} role="alert">Você não possui permissão para editar esta lista.</p>
      ) : null}

      {termo.length >= 2 && termo.length <= 100 ? (
        <>
          {!listaId ? (
            <nav className={styles.buscaCategorias} aria-label="Categorias de busca">
              {(["todos", ...CATEGORIAS] as const).map((tipo) => (
                <Link key={tipo} prefetch={false} href={endereco(tipo)} aria-current={categoria === tipo ? "page" : undefined}>
                  {tipo === "todos" ? "Todos" : TITULOS[tipo]}
                </Link>
              ))}
            </nav>
          ) : null}

          <Suspense fallback={<p className={styles.message}>Buscando música...</p>} key={`${termo}-${categoria}-${pagina}`}>
            <Resultados termo={termo} categoria={categoria} pagina={pagina} listaId={permitida?.id} listaContexto={listaId ?? undefined} />
          </Suspense>
        </>
      ) : <p className={styles.message}>Informe entre 2 e 100 caracteres para pesquisar.</p>}
    </>
  );
}

async function Resultados({
  termo, categoria, pagina, listaId, listaContexto,
}: {
  termo: string;
  categoria: Categoria | "todos";
  pagina: number;
  listaId?: number;
  listaContexto?: number;
}) {
  const categorias = categoria === "todos" ? ["artistas", "albuns", "faixas"] as const : [categoria];
  const secoes = [];

  // Sequencial: nao disputar o mesmo limitador de rede dentro da busca.
  for (const tipo of categorias) {
    const resultado = await buscar(termo, tipo, categoria === "todos" ? 1 : pagina, categoria === "todos" ? 3 : 12);
    const p = new URLSearchParams({ termo, categoria: tipo });
    if (listaContexto) p.set("lista", String(listaContexto));
    const endereco = `/buscar?${p}`;

    secoes.push(
      <section className={styles.results} key={tipo}>
        <div className={styles.tituloDescoberta}>
          <h2>{TITULOS[tipo]}</h2>
          {categoria === "todos" ? <Link prefetch={false} href={endereco}>Ver todos</Link> : null}
        </div>
        {resultado.ok ? (
          <>
            <ResultadosMusicais itens={resultado.dados.resultados} categoria={tipo} listaId={listaId} />
            {categoria !== "todos" ? <Paginacao pagina={pagina} temProxima={resultado.dados.tem_proxima} endereco={endereco} /> : null}
          </>
        ) : <p role="alert" className={styles.message}>{resultado.mensagem}</p>}
      </section>
    );
  }
  return <>{secoes}</>;
}

export default function BuscarPage({ searchParams }: { searchParams: Parametros }) {
  return (
    <main className={styles.container}>
      <section className={styles.searchPage}>
        <span className={styles.accent} aria-hidden="true" />
        <h1>Buscar música</h1>
        <Suspense fallback={<p className={styles.message}>Carregando pesquisa...</p>}>
          <Conteudo searchParams={searchParams} />
        </Suspense>
      </section>
    </main>
  );
}
