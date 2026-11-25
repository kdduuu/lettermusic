import Link from "next/link";
import { Suspense } from "react";
import { redirect } from "next/navigation";
import { requisitarBackend } from "@/lib/backend";
import { CapaAlbum } from "@/components/capa-album";
import { obterCapaAlbum } from "@/lib/catalogo";
import { obterTokenSessao, obterUsuarioAutenticado } from "@/lib/sessao";
import styles from "./page.module.css";

type Parametros = Promise<{
  categoria?: string | string[];
  pagina?: string | string[];
}>;

type Registro = {
  id: number;
  obra_id: number;
  id_musicbrainz: string | null;
  titulo: string | null;
  artista: string | null;
  nota?: number;
  texto?: string;
  ouvida_em?: string;
};

type Categoria = {
  titulo: string;
  caminho: string;
  tipo: "ouvidas" | "favoritos" | "quero-ouvir" | "escutas" | "avaliacoes" | "reviews";
};

const CATEGORIAS: Categoria[] = [
  { titulo: "Já ouvi", caminho: "/interacoes/obras-ouvidas", tipo: "ouvidas" },
  { titulo: "Favoritos", caminho: "/biblioteca/favoritos", tipo: "favoritos" },
  { titulo: "Quero ouvir", caminho: "/biblioteca/quero-ouvir", tipo: "quero-ouvir" },
  { titulo: "Histórico de escutas", caminho: "/interacoes/escutas", tipo: "escutas" },
  { titulo: "Minhas avaliações", caminho: "/interacoes/avaliacoes", tipo: "avaliacoes" },
  { titulo: "Minhas reviews", caminho: "/interacoes/reviews", tipo: "reviews" },
];

async function buscarRegistros(caminho: string, token: string, pagina: number): Promise<Registro[] | null> {
  try {
    const resposta = await requisitarBackend(`${caminho}?pagina=${pagina}&por_pagina=20`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    if (!resposta.ok) return null;
    const dados: unknown = await resposta.json();
    if (!Array.isArray(dados)) return null;
    return dados.filter((item): item is Registro =>
      typeof item === "object" && item !== null &&
      typeof item.id === "number" &&
      typeof item.obra_id === "number" &&
      (item.id_musicbrainz === null || typeof item.id_musicbrainz === "string") &&
      (item.titulo === null || typeof item.titulo === "string") &&
      (item.artista === null || typeof item.artista === "string")
    );
  } catch {
    return null;
  }
}

function Complemento({ registro, tipo }: { registro: Registro; tipo: Categoria["tipo"] }) {
  if (tipo === "avaliacoes" && typeof registro.nota === "number") {
    return <span className={styles.detalhe}>★ {registro.nota.toLocaleString("pt-BR")}</span>;
  }
  if (tipo === "reviews" && typeof registro.texto === "string") {
    return <p className={styles.reviewTexto}>{registro.texto}</p>;
  }
  if (tipo === "escutas" && typeof registro.ouvida_em === "string") {
    const data = new Date(registro.ouvida_em);
    return !Number.isNaN(data.getTime()) ? (
      <span className={styles.detalhe}>
        {new Intl.DateTimeFormat("pt-BR", { dateStyle: "short", timeZone: "America/Sao_Paulo" }).format(data)}
      </span>
    ) : null;
  }
  return null;
}

async function CapasDaColecao({ registros }: { registros: Registro[] }) {
  const albuns = registros.filter(
    (r): r is Registro & { id_musicbrainz: string } =>
      typeof r.id_musicbrainz === "string" &&
      /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i.test(r.id_musicbrainz)
  ).slice(0, 5);
  if (!albuns.length) return <p className={styles.mensagem}>Sem álbuns registrados.</p>;
  const urls = await Promise.all(albuns.map(a => obterCapaAlbum(a.id_musicbrainz)));
  return (
    <div className={styles.vitrineCapas}>
      {albuns.map((album, index) => (
        <Link href={"/albuns/" + encodeURIComponent(album.id_musicbrainz)} key={album.id} className={styles.albumVitrine}>
          <CapaAlbum url={urls[index]} titulo={album.titulo ?? "Álbum"} className={styles.capaVitrine} />
          <strong>{album.titulo ?? "Álbum sem título"}</strong>
          <span>{album.artista ?? "Artista não informado"}</span>
        </Link>
      ))}
    </div>
  );
}

async function ConteudoBiblioteca({
  searchParams,
}: {
  searchParams: Parametros;
}) {
  const usuario = await obterUsuarioAutenticado();
  if (!usuario) redirect("/entrar");

  const token = await obterTokenSessao();
  if (!token) redirect("/entrar");

  const parametros = await searchParams;

  const categoriaAtiva = typeof parametros.categoria === "string" &&
    CATEGORIAS.some(c => c.tipo === parametros.categoria)
    ? parametros.categoria
    : "";

  const numero = typeof parametros.pagina === "string"
    ? parametros.pagina : "";

  const pagina = /^[1-9]\d{0,4}$/.test(numero)
    ? Math.min(10000, Number(numero)) : 1;

  const resultados = await Promise.all(
    CATEGORIAS.map(({ caminho, tipo }) =>
      buscarRegistros(caminho, token, categoriaAtiva === tipo ? pagina : 1)
    ),
  );

  return (
    <>
      <header className={styles.topoBiblioteca}>
        
        <h1>Minha biblioteca</h1>
        
        <nav className={styles.navegacaoCategorias} aria-label="Categorias da biblioteca">
          {CATEGORIAS.map(categoria => (
            <a key={categoria.tipo} href={"#secao-" + categoria.tipo}>{categoria.titulo}</a>
          ))}
        </nav>
      </header>
      <section className={styles.vitrine} aria-label="Capas da minha coleção">
        <div className={styles.vitrineCabecalho}>
          
          <h2>Álbuns ouvidos</h2>
        </div>
        <Suspense fallback={<p className={styles.mensagem}>Carregando capas...</p>}>
          {resultados[0] === null ? <p role="alert" className={styles.mensagem}>Não foi possível carregar os álbuns.</p> : <CapasDaColecao registros={resultados[0]} />}
        </Suspense>
      </section>
      <div className={styles.secoesGrid}>
      {CATEGORIAS.map((categoria, indice) => {
        const itens = resultados[indice];
        const paginaAtual = categoriaAtiva === categoria.tipo ? pagina : 1;
        const temProxima = itens !== null && itens.length === 20;
        const base = `/biblioteca?categoria=${categoria.tipo}&pagina=`;

        return (
          <section
            key={categoria.caminho}
            id={`secao-${categoria.tipo}`}
            className={styles.secao}
          >
            <h2>{categoria.titulo}</h2>
            {itens === null ? (
              <p className={styles.mensagem}>Não foi possível carregar esta seção agora.</p>
            ) : itens.length === 0 ? (
              <p className={styles.mensagem}>Nenhum álbum registrado ainda.</p>
            ) : (
              <ul className={styles.lista}>
                {itens.map((item) => (
                  <li key={`${categoria.tipo}-${item.id}`}>
                    <div className={styles.linha}>
                      {item.id_musicbrainz && /^[a-f0-9-]{36}$/i.test(item.id_musicbrainz) ? (
                        <Link href={`/albuns/${encodeURIComponent(item.id_musicbrainz)}`}>
                          {item.titulo ?? "Álbum sem título"}
                        </Link>
                      ) : <span>{item.titulo ?? "Álbum sem título"}</span>}
                      <span className={styles.artista}>{item.artista ?? "Artista desconhecido"}</span>
                      <Complemento registro={item} tipo={categoria.tipo} />
                    </div>
                  </li>
                ))}
              </ul>
            )}
            {itens !== null && (paginaAtual > 1 || temProxima) ? (
              <nav
                className={styles.paginacao}
                aria-label={`Paginação de ${categoria.titulo}`}
              >
                {paginaAtual > 1 ? (
                  <Link href={`${base}${paginaAtual - 1}#secao-${categoria.tipo}`}>
                    Anterior
                  </Link>
                ) : null}
                <span>Página {paginaAtual}</span>
                {temProxima ? (
                  <Link href={`${base}${paginaAtual + 1}#secao-${categoria.tipo}`}>
                    Próxima
                  </Link>
                ) : null}
              </nav>
            ) : null}
          </section>
        );
      })}
      </div>
      
    </>
  );
}

export default function BibliotecaPage({
  searchParams,
}: {
  searchParams: Parametros;
}) {
  return (
    <main className={styles.container}>
      <Suspense fallback={<p className={styles.mensagem}>Carregando biblioteca...</p>}>
        <ConteudoBiblioteca searchParams={searchParams} />
      </Suspense>
    </main>
  );
}