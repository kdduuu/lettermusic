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
          <span className={styles.etiqueta}>Comunidade</span>
          <h1>Explorar listas</h1>
          <p>
            Descubra coleções musicais criadas por outras pessoas.
          </p>
        </div>
        <Link href="/listas" className={styles.linkPerfil}>
          Minhas listas
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
              ? "Não há mais listas nesta página."
              : "Nenhuma lista pública disponível ainda."}
          </p>
        ) : (
          <ul className={styles.grade}>
            {resultado.dados.resultados.map((lista, indice) => (
              <li key={lista.id}>
                <Link
                  className={styles.cartao}
                  href={`/listas/${lista.id}`}
                >
                  {indice < 8 ? (
                    <Suspense fallback={<div className={styles.icone} aria-hidden="true">♪</div>}>
                      <VitrineLista listaId={lista.id} titulo={lista.titulo} />
                    </Suspense>
                  ) : <div className={styles.previaTipografica} aria-hidden="true"><span>LETTERMUSIC / LISTA</span><strong>{lista.titulo}</strong></div>}
                  <span className={styles.visibilidade}>
                    {lista.total_itens} {lista.total_itens === 1
                      ? "álbum" : "álbuns"}
                  </span>
                  <h3>{lista.titulo}</h3>
                  <p>{lista.descricao || "Seleção musical"}</p>
                </Link>
                <p className={styles.autorPublico}>
                  Por{" "}
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
            aria-label="Páginas de listas públicas"
          >
            {pagina > 1 ? (
              <Link href={`/listas/explorar?pagina=${pagina - 1}`}>
                Anterior
              </Link>
            ) : null}
            <span>Página {pagina}</span>
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
          <p className={styles.vazio}>Carregando listas públicas...</p>
        }
      >
        <Conteudo searchParams={searchParams} />
      </Suspense>
    </main>
  );
}
