import Link from "next/link";
import { Suspense } from "react";
import { CapaAlbum } from "@/components/capa-album";
import { FaixasDoAlbum } from "@/components/exploracao-musical";
import { FormularioInteracoes } from "@/components/formulario-interacoes";
import { FormularioAvaliacao } from "@/components/formulario-avaliacao";
import { FormularioAdicionarAlbum } from "@/components/formularios-listas";
import { detalharAlbum, obterCapaAlbum } from "@/lib/catalogo";
import { obterEstadoAlbum, obterResumoAlbum } from "@/lib/estado-album";
import { obterTokenSessao, obterUsuarioAutenticado } from "@/lib/sessao";
import { listasParaAdicionar } from "@/lib/listas";
import styles from "./page.module.css";

type ParametrosAlbum = Promise<{ id: string }>;

async function CapaDaObra({ id, titulo }: { id: string; titulo: string }) {
  const url = await obterCapaAlbum(id);
  return <CapaAlbum key={id} url={url} titulo={titulo} className={styles.cover} />;
}

async function BlocoSocial({ id }: { id: string }) {
  const [resumo, usuario] = await Promise.all([
    obterResumoAlbum(id),
    obterUsuarioAutenticado(),
  ]);
  const token = usuario ? await obterTokenSessao() : null;
  const [estado, listas] = await Promise.all([
    token ? obterEstadoAlbum(id, token) : Promise.resolve(null),
    token ? listasParaAdicionar(token) : Promise.resolve(null),
  ]);

  return (
    <section className={styles.social} aria-label="Atividade social do álbum">
      <div className={styles.resumo}>
        <h2>Na comunidade</h2>
        {resumo.ok ? (
          resumo.dados.quantidade_avaliacoes > 0 ? (
            <p>
              <strong>{resumo.dados.media_avaliacoes?.toLocaleString("pt-BR")} ★</strong>
              <span> · {resumo.dados.quantidade_avaliacoes} avaliações</span>
            </p>
          ) : <p className={styles.muted}>Este álbum ainda não tem avaliações na comunidade.</p>
        ) : <p className={styles.muted} role="status">{resumo.mensagem}</p>}
      </div>

      {usuario ? (
        estado?.ok ? (
          <div className={styles.interacoes}>
            <FormularioInteracoes id={id} estado={estado.dados} />
            <FormularioAvaliacao id={id} estado={estado.dados} />
          </div>
        ) : <p className={styles.muted} role="status">
          {estado?.mensagem ?? "Não foi possível consultar seus registros."}
        </p>
      ) : (
        <p className={styles.muted}>
          <Link href="/entrar">Entre na sua conta</Link> para avaliar, registrar escutas ou escrever uma review.
        </p>
      )}

      {usuario && listas ? (
        <section className={styles.listasDoAlbum} aria-label="Adicionar a uma lista musical">
          <h2>Suas listas</h2>
          {listas.ok && listas.dados.length ? (
            <FormularioAdicionarAlbum idMusicBrainz={id} listas={listas.dados} />
          ) : (
            <p className={styles.muted}>
              {listas.ok ? "Você ainda não criou uma lista." : listas.mensagem}{" "}
              <Link href="/listas">Gerenciar listas</Link>
            </p>
          )}
          {listas.ok && listas.dados.length > 0 ? (
            <p className={styles.muted}><Link href="/listas">Ver todas as listas</Link></p>
          ) : null}
        </section>
      ) : null}

      <div className={styles.reviews}>
        <h2>Reviews recentes</h2>
        {resumo.ok && resumo.dados.reviews.length ? (
          <ul className={styles.reviewLista}>
            {resumo.dados.reviews.map((review, indice) => (
              <li key={`${review.username}-${review.criada_em}-${indice}`}>
                <p className={styles.reviewAutor}>
                  <Link href={`/usuarios/${encodeURIComponent(review.username)}`}>
                    <strong>{review.nome_exibicao}</strong>
                    <span> @{review.username}</span>
                  </Link>
                </p>
                <p className={styles.reviewTexto}>{review.texto}</p>
              </li>
            ))}
          </ul>
        ) : <p className={styles.muted}>
          {resumo.ok ? "Ainda não há reviews publicadas deste álbum." : "Reviews temporariamente indisponíveis."}
        </p>}
      </div>
    </section>
  );
}

async function ConteudoAlbum({ params }: { params: ParametrosAlbum }) {
  const { id } = await params;
  const resultado = await detalharAlbum(id);

  if (!resultado.ok) {
    return <p className={styles.message} role="alert">{resultado.mensagem}</p>;
  }

  const { obra } = resultado;
  return (
    <>
      <article className={styles.album}>
        <Suspense fallback={<div className={styles.cover} aria-label="Carregando capa">♪</div>}>
          <CapaDaObra id={id} titulo={obra.titulo ?? "Álbum"} />
        </Suspense>
        <div className={styles.info}>
          <span className={styles.accent} aria-hidden="true" />
          <h1>{obra.titulo}</h1>
          <p className={styles.artist}>
            {obra.creditos_artistas?.length ? (
              obra.creditos_artistas.map((credito, indice) => (
                <span key={`${credito.id_musicbrainz}-${indice}`}>
                  {credito.id_musicbrainz ? (
                    <Link prefetch={false} href={`/artistas/${credito.id_musicbrainz}`}>
                      {credito.nome}
                    </Link>
                  ) : credito.nome}
                  {credito.separador}
                </span>
              ))
            ) : obra.artista ?? "Artista não informado"}
          </p>
          <p className={styles.meta}>
            {[obra.data_lancamento?.slice(0, 4), obra.tipo].filter(Boolean).join(" · ")}
          </p>
        </div>
      </article>
      <div className={styles.corpoAlbum}>
        <div className={styles.colunaFaixas}>
          <Suspense fallback={<p className={styles.message}>Carregando faixas...</p>}>
            <FaixasDoAlbum id={id} />
          </Suspense>
        </div>
        <aside className={styles.colunaSocial}>
          <Suspense fallback={<p className={styles.message}>Carregando atividade musical...</p>}>
            <BlocoSocial id={id} />
          </Suspense>
        </aside>
      </div>
    </>
  );
}

export default function AlbumPage({ params }: { params: ParametrosAlbum }) {
  return (
    <main className={styles.container}>
      <Link href="/" className={styles.back}>Início</Link>
      <Suspense fallback={<p className={styles.message}>Carregando álbum...</p>}>
        <ConteudoAlbum params={params} />
      </Suspense>
    </main>
  );
}