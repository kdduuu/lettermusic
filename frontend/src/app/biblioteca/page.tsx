import Link from "next/link";
import { Suspense } from "react";
import { redirect } from "next/navigation";
import { requisitarBackend } from "@/lib/backend";
import { obterTokenSessao, obterUsuarioAutenticado } from "@/lib/sessao";
import styles from "./page.module.css";

type Registro = {
  obra_id: number;
  id_musicbrainz: string | null;
  titulo: string | null;
  artista: string | null;
};

type Categoria = {
  titulo: string;
  caminho: string;
};

const CATEGORIAS: Categoria[] = [
  { titulo: "Já ouvi", caminho: "/interacoes/obras-ouvidas" },
  { titulo: "Favoritos", caminho: "/biblioteca/favoritos" },
  { titulo: "Quero ouvir", caminho: "/biblioteca/quero-ouvir" },
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
      typeof item.obra_id === "number" &&
      (item.id_musicbrainz === null || typeof item.id_musicbrainz === "string") &&
      (item.titulo === null || typeof item.titulo === "string") &&
      (item.artista === null || typeof item.artista === "string")
    );
  } catch {
    return null;
  }
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
                  <li key={item.obra_id}>
                    {item.id_musicbrainz && /^[a-f0-9-]{36}$/i.test(item.id_musicbrainz) ? (
                      <Link href={`/albuns/${encodeURIComponent(item.id_musicbrainz)}`}>
                        {item.titulo ?? "Álbum sem título"}
                      </Link>
                    ) : (
                      <span>{item.titulo ?? "Álbum sem título"}</span>
                    )}
                    <span className={styles.artista}>{item.artista ?? "Artista desconhecido"}</span>
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