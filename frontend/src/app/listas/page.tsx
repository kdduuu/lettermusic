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
          <span className={styles.etiqueta}>Sua coleção</span>
          <h1>Listas musicais</h1>
          
        </div>
        <Link href={`/usuarios/${encodeURIComponent(usuario.username)}`} className={styles.linkPerfil}>Meu perfil</Link>
      </div>

      <details className={styles.nova}>
        <summary>+ Criar nova lista</summary>
        <div className={styles.formulario}><FormularioCriarLista /></div>
      </details>

      <section className={styles.listagem} aria-labelledby="minhas-listas">
        <h2 id="minhas-listas">Minhas listas</h2>
        {!resultado.ok ? (
          <p role="alert" className={styles.erro}>{resultado.mensagem}</p>
        ) : resultado.dados.listas.length === 0 ? (
          <p className={styles.vazio}>{pagina > 1 ? "Não há mais listas nesta página." : "Nenhuma lista ainda. Crie a primeira acima!"}</p>
        ) : (
          <ul className={styles.grade}>
            {resultado.dados.listas.map((lista) => (
              <li key={lista.id}>
                <Link className={styles.cartao} href={`/listas/${lista.id}`}>
                  {(
                    <Suspense fallback={null}>
                      <VitrineLista listaId={lista.id} token={token} titulo={lista.titulo} />
                    </Suspense>
                  )}
                  <span className={styles.visibilidade}>{lista.publica ? "Pública" : "Privada"}</span>
                  <h3>{lista.titulo}</h3>
                  {lista.descricao ? <p>{lista.descricao}</p> : null}
                </Link>
              </li>
            ))}
          </ul>
        )}
        {resultado.ok && (pagina > 1 || resultado.dados.temProxima) ? (
          <nav className={styles.paginacao} aria-label="Páginas de listas">
            {pagina > 1 ? <Link href={`/listas?pagina=${pagina - 1}`}>Anterior</Link> : null}
            <span>Página {pagina}</span>
            {resultado.dados.temProxima ? <Link href={`/listas?pagina=${pagina + 1}`}>Próxima</Link> : null}
          </nav>
        ) : null}
      </section>
    </>
  );
}

export default function ListasPage({ searchParams }: { searchParams: Parametros }) {
  return (
    <main className={styles.container}>
      <Suspense fallback={<p className={styles.vazio}>Carregando suas listas...</p>}>
        <Conteudo searchParams={searchParams} />
      </Suspense>
    </main>
  );
}