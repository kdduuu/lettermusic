import Link from "next/link";
import { Suspense } from "react";
import { Paginacao, ResultadosMusicais } from "@/components/exploracao-musical";
import { buscar, obterPagina, type Categoria, type Item } from "@/lib/exploracao";
import { MBID_VALIDO } from "@/lib/estado-album";
import { TentarNovamente } from "@/components/tentar-novamente";
import { idPositivo, verificarMinhaLista } from "@/lib/listas";
import { obterTokenSessao } from "@/lib/sessao";
import styles from "../page.module.css";

type Parametros = Promise<{
  termo?: string | string[];
  categoria?: string | string[];
  pagina?: string | string[];
  lista?: string | string[];
  artista?: string | string[];
}>;

const CATEGORIAS: Categoria[] = ["albuns", "artistas", "faixas"];
const TITULOS = { albuns: "Albums", artistas: "Artists", faixas: "Tracks" };

async function Conteudo({ searchParams }: { searchParams: Parametros }) {
  const params = await searchParams;
  const termo = typeof params.termo === "string" ? params.termo.trim() : "";
  const listaId = idPositivo(typeof params.lista === "string" ? params.lista : undefined);
  const categoria = !listaId && CATEGORIAS.includes(params.categoria as Categoria)
    ? params.categoria as Categoria : listaId ? "albuns" : "todos";

  const pagina = obterPagina(params.pagina);
  const artistaId = !listaId && categoria !== "todos" &&
    categoria !== "artistas" && typeof params.artista === "string" &&
    MBID_VALIDO.test(params.artista) ? params.artista : undefined;
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
        <label htmlFor="busca-exploracao" className={styles.visuallyHidden}>Search music</label>
        {listaId ? <input type="hidden" name="lista" value={listaId} /> : null}
        {categoria !== "todos" ? <input type="hidden" name="categoria" value={categoria} /> : null}
        <div>
          <input id="busca-exploracao" name="termo" type="search" defaultValue={termo} required minLength={2} maxLength={100} placeholder="Album, artist or track…" />
          <button type="submit">Search</button>
        </div>
      </form>

      {permitida ? (
        <p className={styles.message}>Adding to <Link href={`/listas/${permitida.id}`}>{permitida.titulo}</Link>.</p>
      ) : listaId ? (
        <p className={styles.message} role="alert">You cannot edit this list.</p>
      ) : null}

      {termo.length >= 2 && termo.length <= 100 ? (
        <>
          {!listaId ? (
            <nav className={styles.buscaCategorias} aria-label="Search categories">
              {(["todos", ...CATEGORIAS] as const).map((tipo) => (
                <Link key={tipo} prefetch={false} href={endereco(tipo)} aria-current={categoria === tipo ? "page" : undefined}>
                  {tipo === "todos" ? "All" : TITULOS[tipo]}
                </Link>
              ))}
            </nav>
          ) : null}

          <Suspense fallback={<p className={styles.message}>Searching…</p>} key={`${termo}-${categoria}-${pagina}-${artistaId ?? ""}`}>
            <Resultados termo={termo} categoria={categoria} pagina={pagina} listaId={permitida?.id} listaContexto={listaId ?? undefined} artistaId={artistaId} />
          </Suspense>
        </>
      ) : null}
    </>
  );
}

type Consulta = Awaited<ReturnType<typeof buscar>>;

function normalizar(texto: string) {
  return texto.normalize("NFKD")
    .replace(/\p{M}/gu, "")
    .toLowerCase()
    .replace(/[^\p{L}\p{N}]+/gu, " ")
    .trim();
}

// Contexto aproximado conservador: uma alteracao em palavra longa.
function quaseIgual(a: string, b: string) {
  if (a.length < 5 || b.length < 5 || a.includes(" ") ||
      b.includes(" ") || a[0] !== b[0] ||
      Math.abs(a.length - b.length) > 1) return false;

  let i = 0;
  let j = 0;
  let erros = 0;

  while (i < a.length && j < b.length) {
    if (a[i] === b[j]) {
      i++;
      j++;
      continue;
    }

    if (++erros > 1) return false;

    if (a.length >= b.length) i++;
    if (b.length >= a.length) j++;
  }

  return erros + (a.length - i) + (b.length - j) <= 1;
}

function escolherArtista(
  resultado: Consulta,
  termo: string,
): Item | null {
  if (!resultado.ok) return null;

  const primeiro = resultado.dados.resultados[0];
  if (!primeiro) return null;

  const busca = normalizar(termo);
  const nome = normalizar(primeiro.titulo);

  if (busca === nome) return primeiro;

  if (quaseIgual(busca, nome)) {
    const ambiguo = resultado.dados.resultados.slice(1).some(item => {
      const outro = normalizar(item.titulo);
      return outro === busca || outro === nome || quaseIgual(busca, outro);
    });

    if (!ambiguo) return primeiro;
  }

  return null;
}

async function SecaoResultado({
  tarefa, termo, tipo, geral, pagina,
  listaId, endereco, contexto, artistaId,
}: {
  tarefa: Promise<Consulta>;
  termo: string;
  tipo: Categoria;
  geral: boolean;
  pagina: number;
  listaId?: number;
  endereco: string;
  contexto?: Promise<Item | null>;
  artistaId?: string;
}) {
  const resultado = await tarefa;
  const artista = contexto ? await contexto : null;

  if (geral && resultado.ok && !resultado.dados.resultados.length) {
    return null;
  }

  const itens = resultado.ok ? resultado.dados.resultados : [];
  const primeiro = itens[0];

  const destaque = geral && tipo === "artistas" &&
    primeiro && artista?.id_musicbrainz === primeiro.id_musicbrainz;

  const vinculo = tipo !== "artistas"
    ? artista?.id_musicbrainz ?? artistaId
    : undefined;

  const enderecoContextual = vinculo
    ? `${endereco}&artista=${encodeURIComponent(vinculo)}`
    : endereco;

  const tituloSecao = destaque
    ? "Other artists"
    : artista && tipo !== "artistas"
      ? `${TITULOS[tipo]} by ${artista.titulo}`
      : TITULOS[tipo];

  return (
    <section className={styles.results}>
      {destaque ? (
        <>
          <h2>
            {normalizar(primeiro.titulo) === normalizar(termo)
              ? "Top match"
              : "Suggested artist"}
          </h2>
          <ResultadosMusicais itens={[primeiro]} categoria="artistas" />
        </>
      ) : null}

      {(!destaque || itens.length > 1 ||
        (resultado.ok && resultado.dados.tem_proxima)) ? (
        <div className={styles.tituloDescoberta}>
          <h2>{tituloSecao}</h2>
          {geral && resultado.ok &&
            (resultado.dados.tem_proxima || Boolean(vinculo)) ? (
              <Link prefetch={false} href={enderecoContextual}>
                View all
              </Link>
            ) : null}
        </div>
      ) : null}

      {!geral && vinculo ? (
        <p className={styles.notaExploracao}>
          Results for selected artist.{" "}
          <Link prefetch={false} href={endereco}>
            Search all artists
          </Link>
        </p>
      ) : null}

      {resultado.ok ? (
        <>
          {destaque && itens.length === 1 ? null : (
            <ResultadosMusicais
              itens={destaque ? itens.slice(1) : itens}
              categoria={tipo}
              listaId={listaId}
            />
          )}

          {!geral && tipo === "albuns" && itens.length === 0 ? (
            <p className={styles.message}>
              Missing an album?{" "}
              <Link
                href="https://musicbrainz.org/release/add"
                target="_blank"
                rel="noopener noreferrer"
              >
                Add release to MusicBrainz
              </Link>
              .
            </p>
          ) : null}

          {!geral ? (
            <>

              <Paginacao
                pagina={pagina}
                temProxima={resultado.dados.tem_proxima}
                endereco={enderecoContextual}
              />
            </>
          ) : null}
        </>
      ) : (
        <p role="alert" className={styles.message}>
          {resultado.mensagem}{" "}
          <TentarNovamente />
        </p>
      )}
    </section>
  );
}

async function AvisoSemResultados({
  tarefas,
}: {
  tarefas: Promise<Consulta>[];
}) {
  const resultados = await Promise.all(tarefas);

  return resultados.every(r => r.ok && r.dados.resultados.length === 0)
    ? <p className={styles.message}>
        No results found.{" "}
        <Link
          href="https://musicbrainz.org/release/add"
          target="_blank"
          rel="noopener noreferrer"
        >
          Add release to MusicBrainz
        </Link>.
      </p>
    : null;
}

function Resultados({
  termo, categoria, pagina,
  listaId, listaContexto, artistaId,
}: {
  termo: string;
  categoria: Categoria | "todos";
  pagina: number;
  listaId?: number;
  listaContexto?: number;
  artistaId?: string;
}) {
  const geral = categoria === "todos";

  const categorias: readonly Categoria[] = categoria === "todos"
    ? ["artistas", "albuns", "faixas"]
    : [categoria];

  let anterior: Promise<unknown> = Promise.resolve();
  let contexto: Promise<Item | null> = Promise.resolve(null);

  const tarefas = categorias.map(tipo => {
    // Captura o contexto anterior para evitar dependencias circulares.
    const contextoAnterior = contexto;

    const tarefa = anterior.then(async () => {
      const escolhido = geral && tipo !== "artistas"
        ? await contextoAnterior
        : null;

      return buscar(
        termo,
        tipo,
        geral ? 1 : pagina,
        geral ? 3 : 12,
        escolhido?.id_musicbrainz ?? artistaId,
      );
    });

    if (geral && tipo === "artistas") {
      contexto = tarefa.then(resultado =>
        escolherArtista(resultado, termo)
      );
    }

    anterior = tarefa;

    return {
      tipo,
      tarefa,
      contexto: geral ? contexto : undefined,
    };
  });

  return (
    <>
      {tarefas.map(({ tipo, tarefa, contexto }) => {
        const p = new URLSearchParams({
          termo,
          categoria: tipo,
        });

        if (listaContexto) {
          p.set("lista", String(listaContexto));
        }

        return (
          <Suspense key={tipo} fallback={
            <p className={styles.message}>
              Searching {TITULOS[tipo].toLowerCase()}…
            </p>
          }>
            <SecaoResultado
              tarefa={tarefa}
              termo={termo}
              tipo={tipo}
              geral={geral}
              pagina={pagina}
              listaId={listaId}
              endereco={`/buscar?${p}`}
              contexto={contexto}
              artistaId={artistaId}
            />
          </Suspense>
        );
      })}

      {geral ? (
        <Suspense fallback={null}>
          <AvisoSemResultados tarefas={tarefas.map(t => t.tarefa)} />
        </Suspense>
      ) : null}
    </>
  );
}

export default function BuscarPage({ searchParams }: { searchParams: Parametros }) {
  return (
    <main className={styles.container}>
      <section className={styles.searchPage}>
        <h1>Search</h1>
        <Suspense fallback={<p className={styles.message}>Loading search…</p>}>
          <Conteudo searchParams={searchParams} />
        </Suspense>
      </section>
    </main>
  );
}
