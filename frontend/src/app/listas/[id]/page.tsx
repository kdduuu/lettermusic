import Link from "next/link";
import { notFound } from "next/navigation";
import { Suspense } from "react";
import { CapaAlbum } from "@/components/capa-album";
import {
  ControlesItemLista,
  FormularioEditarLista,
  FormularioExcluirLista,
} from "@/components/formularios-listas";
import { obterCapaAlbum } from "@/lib/catalogo";
import { detalheLista, idPositivo, type ItemLista } from "@/lib/listas";
import { obterTokenSessao } from "@/lib/sessao";
import styles from "./page.module.css";

type Parametros = Promise<{ id: string }>;
type Filtros = Promise<{ pagina?: string | string[] }>;

async function Colagem({ itens }: { itens: ItemLista[] }) {
  const capas = itens.slice(0, 4);
  const urls = await Promise.all(capas.map((item) =>
    item.id_musicbrainz ? obterCapaAlbum(item.id_musicbrainz) : Promise.resolve(null)
  ));
  return (
    <div className={styles.colagem} aria-label="Capas dos primeiros álbuns da lista">
      {Array.from({ length: 4 }, (_, i) => {
        const item = capas[i];
        if (!item?.id_musicbrainz) {
          return <div key={i} className={styles.capaColagem} aria-hidden="true">♪</div>;
        }
        return (
          <Link key={item.id} href={"/albuns/" + encodeURIComponent(item.id_musicbrainz)}>
            <CapaAlbum url={urls[i]} titulo={item.titulo ?? "Álbum"} className={styles.capaColagem} />
          </Link>
        );
      })}
    </div>
  );
}

async function GradeDeAlbuns({
  itens, dono, listaId, ultimaPosicao, temProxima, pagina,
}: {
  itens: ItemLista[];
  dono: boolean;
  listaId: number;
  ultimaPosicao: number;
  temProxima: boolean;
  pagina: number;
}) {
  // A consulta de capas é opcional e não altera nem registra as obras.
  const ids = Array.from(new Set(
    itens.flatMap((item) => item.id_musicbrainz ? [item.id_musicbrainz] : [])
  ));
  const pares = await Promise.all(ids.map(async (id) => [id, await obterCapaAlbum(id)] as const));
  const urls = new Map(pares);
  return (
    <ol className={styles.gradeAlbuns} start={(pagina - 1) * 50 + 1}>
      {itens.map((item) => (
        <li key={item.id} className={styles.cardAlbum}>
          <span className={styles.numero}>{String(item.posicao).padStart(2, "0")}</span>
          {item.id_musicbrainz ? (
            <Link className={styles.linkCapa} href={"/albuns/" + encodeURIComponent(item.id_musicbrainz)}>
              <CapaAlbum
                url={urls.get(item.id_musicbrainz) ?? null}
                titulo={item.titulo ?? "Álbum"}
                className={styles.capaAlbum}
              />
            </Link>
          ) : <div className={styles.capaAlbum} aria-hidden="true">♪</div>}
          <div className={styles.detalheAlbum}>
            <h3>
              {item.id_musicbrainz ? (
                <Link href={"/albuns/" + encodeURIComponent(item.id_musicbrainz)}>
                  {item.titulo ?? "Álbum sem título"}
                </Link>
              ) : <span>{item.titulo ?? "Álbum sem título"}</span>}
            </h3>
            <p>{item.artista ?? "Artista não informado"}</p>
          </div>
          {dono ? (
            <div className={styles.acoesAlbum}>
              <ControlesItemLista
                key={item.id + "-" + item.posicao}
                listaId={listaId}
                obraId={item.obra_id}
                posicao={item.posicao}
                podeDescer={item.posicao < ultimaPosicao || temProxima}
              />
            </div>
          ) : null}
        </li>
      ))}
    </ol>
  );
}

async function Conteudo({ params, searchParams }: { params: Parametros; searchParams: Filtros }) {
  const [parametros, filtros, token] = await Promise.all([
    params, searchParams, obterTokenSessao(),
  ]);
  const id = idPositivo(parametros.id);
  if (!id) notFound();
  const textoPagina = Array.isArray(filtros.pagina) ? filtros.pagina[0] : filtros.pagina;
  const pagina = textoPagina && /^[1-9]\d{0,5}$/.test(textoPagina) ? Number(textoPagina) : 1;
  const resultado = await detalheLista(id, token, pagina);
  if (!resultado.ok) {
    if (resultado.status === 404) notFound();
    return <p role="alert" className={styles.erro}>{resultado.mensagem}</p>;
  }
  const { lista, itens, destaques, dono, temProxima } = resultado.dados;
  const ultimaPosicao = itens.length ? itens[itens.length - 1].posicao : 0;

  return (
    <>
      <nav className={styles.breadcrumb} aria-label="Navegação">
        <Link href={dono ? "/listas" : "/"}>{dono ? "Minhas listas" : "Descobrir"}</Link>
        <span aria-hidden="true">/</span><span>{lista.titulo}</span>
      </nav>

      <section className={styles.hero} aria-labelledby="titulo-lista">
        <Suspense fallback={<div className={styles.espera}>Carregando capas...</div>}>
          <Colagem itens={destaques} />
        </Suspense>
        <div className={styles.info}>
          <span className={styles.traco} aria-hidden="true" />
          <p className={styles.etiqueta}>{lista.publica ? "Coleção pública" : "Coleção privada"}</p>
          <h1 id="titulo-lista">{lista.titulo}</h1>
          {lista.descricao ? <p className={styles.descricao}>{lista.descricao}</p> : (
            <p className={styles.descricaoAlternativa}>Uma seleção de álbuns reunidos em um só lugar.</p>
          )}
          <p className={styles.meta}>Página {pagina} · {itens.length} álbuns exibidos</p>
          <a className={styles.ancoraAlbuns} href="#albuns-lista">Explorar álbuns <span aria-hidden="true">↘</span></a>
        </div>
      </section>

      {dono ? (
        <section className={styles.edicao} aria-label="Gerenciar minha lista">
          <details>
            <summary>Editar informações e privacidade</summary>
            <div className={styles.editar}>
              <FormularioEditarLista key={lista.atualizada_em ?? lista.criada_em} lista={lista} />
              <FormularioExcluirLista id={lista.id} />
            </div>
          </details>
          <form action="/buscar" method="get" role="search" className={styles.buscar}>
            <input type="hidden" name="lista" value={lista.id} />
            <label htmlFor="buscar-lista">Adicionar um álbum à coleção</label>
            <div className={styles.buscarLinha}>
              <input id="buscar-lista" name="termo" type="search" minLength={2} maxLength={100} required placeholder="Pesquise um álbum no MusicBrainz..." />
              <button type="submit">Buscar</button>
            </div>
          </form>
        </section>
      ) : null}

      <section className={styles.conteudo} aria-labelledby="albuns-lista">
        <div className={styles.cabecalhoGrade}>
          <div>
            <p className={styles.etiqueta}>Seleção musical</p>
            <h2 id="albuns-lista">Álbuns da lista</h2>
          </div>
          <span className={styles.contagem}>Ordem da coleção · página {pagina}</span>
        </div>
        {itens.length ? (
          <Suspense fallback={<p className={styles.vazio}>Carregando grade de álbuns...</p>}>
            <GradeDeAlbuns
              itens={itens} dono={dono} listaId={lista.id}
              ultimaPosicao={ultimaPosicao} temProxima={temProxima} pagina={pagina}
            />
          </Suspense>
        ) : <p className={styles.vazio}>Esta lista ainda não tem álbuns nesta página.</p>}

        {pagina > 1 || temProxima ? (
          <nav className={styles.paginacao} aria-label="Páginas da lista">
            {pagina > 1 ? <Link href={"/listas/" + lista.id + "?pagina=" + (pagina - 1)}>← Anterior</Link> : null}
            <span>Página {pagina}</span>
            {temProxima ? <Link href={"/listas/" + lista.id + "?pagina=" + (pagina + 1)}>Próxima →</Link> : null}
          </nav>
        ) : null}
      </section>
    </>
  );
}

export default function ListaDetalhePage({ params, searchParams }: { params: Parametros; searchParams: Filtros }) {
  return (
    <main className={styles.container}>
      <div className={styles.interior}>
        <Suspense fallback={<p className={styles.vazio}>Carregando lista musical...</p>}>
          <Conteudo params={params} searchParams={searchParams} />
        </Suspense>
      </div>
    </main>
  );
}
