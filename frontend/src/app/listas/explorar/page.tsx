import Link from "next/link";
import { Suspense } from "react";
import { obterListasPublicas } from "@/lib/listas-publicas";
import { VitrineLista } from "@/components/vitrine-lista";
import styles from "../page.module.css";

type Parametros = Promise<{
  pagina?: string | string[];
}>;

async function Conteudo({
  searchParams,
}: {
  searchParams: Parametros;
}) {
  const parametros = await searchParams;

  const numero = typeof parametros.pagina === "string"
    ? parametros.pagina : "";

  const pagina = /^[1-9]\d{0,4}$/.test(numero)
    ? Math.min(10000, Number(numero)) : 1;

  const resultado = await obterListasPublicas(pagina);

  return (
    <>
      <div className={styles.cabecalho}>
        <div>
          
          <h1>Lists</h1>
          
        </div>
        <Link href="/listas" className={styles.linkPerfil}>
          My lists
        </Link>
      </div>

      <section className={styles.listagem}>
        {!resultado.ok ? (
          <p role="alert" className={styles.erro}>
            {resultado.mensagem}
          </p>
        ) : resultado.dados.resultados.length === 0 ? (
          <p className={styles.vazio}>
            {pagina > 1
              ? "No more lists."
              : "No public lists yet."}
          </p>
        ) : (
          <ul className={styles.grade}>
            {resultado.dados.resultados.map((lista) => (
              <li key={lista.id}>
                <Link
                  className={styles.cartao}
                  href={`/listas/${lista.id}`}
                >
                  <VitrineLista listaId={lista.id} titulo={lista.titulo} />
                  <span className={styles.visibilidade}>
                    {lista.total_itens} {lista.total_itens === 1
                      ? "album" : "albums"}
                  </span>
                  <h3>{lista.titulo}</h3>
                  
                </Link>
                <p className={styles.autorPublico}>
                  By{" "}
                  <Link href={`/usuarios/${encodeURIComponent(lista.username)}`}>
                    {lista.nome_exibicao}
                  </Link>
                </p>
              </li>
            ))}
          </ul>
        )}

        {resultado.ok &&
          (pagina > 1 || resultado.dados.tem_proxima) ? (
          <nav
            className={styles.paginacao}
            aria-label="Public list pages"
          >
            {pagina > 1 ? (
              <Link href={`/listas/explorar?pagina=${pagina - 1}`}>
                Anterior
              </Link>
            ) : null}
            <span>Page {pagina}</span>
            {resultado.dados.tem_proxima ? (
              <Link href={`/listas/explorar?pagina=${pagina + 1}`}>
                Próxima
              </Link>
            ) : null}
          </nav>
        ) : null}
      </section>
    </>
  );
}

export default function ExplorarListasPage({
  searchParams,
}: {
  searchParams: Parametros;
}) {
  return (
    <main className={styles.container}>
      <Suspense
        fallback={
          <p className={styles.vazio}>Loading lists…</p>
        }
      >
        <Conteudo searchParams={searchParams} />
      </Suspense>
    </main>
  );
}
