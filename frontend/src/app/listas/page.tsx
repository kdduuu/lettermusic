import { UiIcon } from "@/components/ui-icon";
import Link from "next/link";
import { redirect } from "next/navigation";
import { Suspense } from "react";
import { FormularioCriarLista } from "@/components/formularios-listas";
import { VitrineLista } from "@/components/vitrine-lista";
import { minhasListas } from "@/lib/listas";
import { obterTokenSessao, obterUsuarioAutenticado } from "@/lib/sessao";
import styles from "./page.module.css";

type Parametros = Promise<{ pagina?: string | string[] }>;

async function Conteudo({ searchParams }: { searchParams: Parametros }) {
  const [usuario, token, parametros] = await Promise.all([
    obterUsuarioAutenticado(), obterTokenSessao(), searchParams,
  ]);
  if (!usuario || !token) redirect("/entrar");

  const numero = Array.isArray(parametros.pagina) ? parametros.pagina[0] : parametros.pagina;
  const pagina = numero && /^[1-9]\d{0,5}$/.test(numero) ? Number(numero) : 1;
  const resultado = await minhasListas(token, pagina);

  return (
    <>
      <div className={styles.cabecalho}>
        <div>
          
          <h1>My lists</h1>
          
        </div>
        <Link href={`/usuarios/${encodeURIComponent(usuario.username)}`} className={styles.linkPerfil}>My profile</Link>
      </div>

      <details className={styles.nova}>
        <summary aria-label="New list" title="New list"><UiIcon name="plus"/></summary>
        <div className={styles.formulario}><FormularioCriarLista /></div>
      </details>

      <section className={styles.listagem} aria-label="My lists">
        {!resultado.ok ? (
          <p role="alert" className={styles.erro}>{resultado.mensagem}</p>
        ) : resultado.dados.listas.length === 0 ? (
          <p className={styles.vazio}>{pagina > 1 ? "No more lists." : "No lists yet."}</p>
        ) : (
          <ul className={styles.grade}>
            {resultado.dados.listas.map((lista) => (
              <li key={lista.id}>
                <Link className={styles.cartao} href={`/listas/${lista.id}`}>
                  <VitrineLista listaId={lista.id} titulo={lista.titulo} />
                  <span className={styles.visibilidade}>{lista.publica ? "Public" : "Private"}</span>
                  <h3>{lista.titulo}</h3>
                  
                </Link>
              </li>
            ))}
          </ul>
        )}
        {resultado.ok && (pagina > 1 || resultado.dados.temProxima) ? (
          <nav className={styles.paginacao} aria-label="List pages">
            {pagina > 1 ? <Link href={`/listas?pagina=${pagina - 1}`}>Previous</Link> : null}
            <span>Page {pagina}</span>
            {resultado.dados.temProxima ? <Link href={`/listas?pagina=${pagina + 1}`}>Next</Link> : null}
          </nav>
        ) : null}
      </section>
    </>
  );
}

export default function ListasPage({ searchParams }: { searchParams: Parametros }) {
  return (
    <main className={styles.container}>
      <Suspense fallback={<p className={styles.vazio}>Loading lists…</p>}>
        <Conteudo searchParams={searchParams} />
      </Suspense>
    </main>
  );
}