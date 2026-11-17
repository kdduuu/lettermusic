import Link from "next/link";
import { Suspense } from "react";
import { redirect } from "next/navigation";
import { requisitarBackend } from "@/lib/backend";
import { obterTokenSessao, obterUsuarioAutenticado } from "@/lib/sessao";
import styles from "./page.module.css";

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

async function buscarRegistros(caminho: string, token: string): Promise<Registro[] | null> {
  try {
    const resposta = await requisitarBackend(`${caminho}?pagina=1&por_pagina=50`, {
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

async function ConteudoBiblioteca() {
  const usuario = await obterUsuarioAutenticado();
  if (!usuario) redirect("/entrar");

  const token = await obterTokenSessao();
  if (!token) redirect("/entrar");

  const resultados = await Promise.all(
    CATEGORIAS.map(({ caminho }) => buscarRegistros(caminho, token)),
  );

  return (
    <>
      <h1>Minha biblioteca</h1>
      <p className={styles.subtitulo}>Seus registros musicais, {usuario.nome_exibicao}.</p>
      {CATEGORIAS.map((categoria, indice) => {
        const itens = resultados[indice];
        return (
          <section key={categoria.caminho} className={styles.secao}>
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
          </section>
        );
      })}
      <p className={styles.limite}>Exibindo até 50 registros recentes por categoria.</p>
    </>
  );
}

export default function BibliotecaPage() {
  return (
    <main className={styles.container}>
      <Suspense fallback={<p className={styles.mensagem}>Carregando biblioteca...</p>}>
        <ConteudoBiblioteca />
      </Suspense>
    </main>
  );
}