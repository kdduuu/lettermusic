import Link from "next/link";
import { Suspense } from "react";
import { CapaAlbum } from "@/components/capa-album";
import { obterCapaAlbum } from "@/lib/catalogo";
import { consultarComunidade, type Atividade, type ObraEmAlta } from "@/lib/comunidade";
import styles from "./page.module.css";

function formatarData(data: string) {
  const partes = /^(\d{4})-(\d{2})-(\d{2})/.exec(data);
  return partes ? `${partes[3]}/${partes[2]}/${partes[1]}` : "";
}
function plural(n: number, singular: string, plural: string) {
  return `${n} ${n === 1 ? singular : plural}`;
}
function perfil(username: string) {
  return `/usuarios/${encodeURIComponent(username)}`;
}
function album(id: string) {
  return `/albuns/${encodeURIComponent(id)}`;
}

function ItemAtividade({ item }: { item: Atividade }) {
  return (
    <li className={styles.atividade}>
      <div className={styles.avatar} aria-hidden="true">{Array.from(item.nome_exibicao.trim())[0]?.toLocaleUpperCase("pt-BR") || "♪"}</div>
      <article>
        <p className={styles.meta}>
          <Link href={perfil(item.username)}>{item.nome_exibicao}</Link> · <time dateTime={item.criada_em}>{formatarData(item.criada_em)}</time>
        </p>
        {item.tipo === "lista" ? (
          <p>Lista pública: <Link href={`/listas/${item.id}`}>{item.titulo}</Link></p>
        ) : (
          <>
            <p>{item.tipo === "review" ? "Publicou uma review de " : "Avaliou "}<Link href={album(item.id_musicbrainz)}>{item.titulo}</Link>{item.artista ? ` — ${item.artista}` : ""}</p>
            {item.tipo === "review" ? (
              <><p className={styles.resumo}>{item.texto}</p><Link className={styles.linkSecundario} href={album(item.id_musicbrainz)}>Ver álbum e reviews</Link></>
            ) : <p className={styles.nota}>★ {item.nota.toLocaleString("pt-BR", { maximumFractionDigits: 1 })}/5</p>}
          </>
        )}
      </article>
    </li>
  );
}

async function EmAlta({ obras }: { obras: ObraEmAlta[] }) {
  const capas = await Promise.all(obras.map((obra) => obterCapaAlbum(obra.id_musicbrainz)));
  return <ul className={styles.obras}>
    {obras.map((obra, i) => (
      <li key={obra.id_musicbrainz}>
        <Link href={album(obra.id_musicbrainz)} className={styles.obra}>
          <CapaAlbum url={capas[i]} titulo={obra.titulo} className={styles.capa} />
          <div><strong>{obra.titulo}</strong><p>{obra.artista ?? "Artista não informado"}</p></div>
        </Link>
        <p className={styles.meta}>{plural(obra.contribuicoes, "contribuição", "contribuições")} · {plural(obra.membros, "membro", "membros")}</p>
      </li>
    ))}
  </ul>;
}

async function ConteudoComunidade() {
  const resultado = await consultarComunidade();
  if (!resultado.ok) return <p role="alert" className={styles.mensagem}>{resultado.mensagem}</p>;
  const { dados } = resultado;
  return (
    <div className={styles.layout}>
      <section aria-labelledby="atividades">
        <h2 id="atividades">Atividades recentes</h2>
        {dados.atividades.length ? <ul className={styles.atividades}>
          {dados.atividades.map((item) => <ItemAtividade key={`${item.tipo}-${item.id}`} item={item} />)}
        </ul> : <p className={styles.mensagem}>Ainda não há atividades públicas.</p>}
        <Link href="/reviews" className={styles.linkSecundario}>Ver todas as reviews</Link>
      </section>
      <aside className={styles.lateral} aria-label="Destaques da comunidade">
        <section aria-labelledby="membros">
          <h2 id="membros">Membros ativos</h2>
          <p className={styles.mensagem}>Contribuições públicas nos últimos {dados.janela_dias} dias.</p>
          {dados.membros_ativos.length ? <ul className={styles.membros}>
            {dados.membros_ativos.map((membro) => (
              <li key={membro.username}>
                <Link href={perfil(membro.username)}>{membro.nome_exibicao}</Link>
                <p className={styles.meta}>@{membro.username} · {plural(membro.contribuicoes, "contribuição", "contribuições")}</p>
              </li>
            ))}
          </ul> : <p className={styles.mensagem}>Nenhuma contribuição no período.</p>}
        </section>
        <section aria-labelledby="em-alta">
          <h2 id="em-alta">Em alta</h2>
          <p className={styles.mensagem}>Avaliações e reviews dos últimos {dados.janela_dias} dias.</p>
          {dados.em_alta.length ? <Suspense fallback={<p className={styles.mensagem}>Carregando capas...</p>}><EmAlta obras={dados.em_alta} /></Suspense> : <p className={styles.mensagem}>Nenhum destaque no período.</p>}
        </section>
      </aside>
    </div>
  );
}

export default function ComunidadePage() {
  return (
    <main className={styles.container}>
      <header className={styles.cabecalho}>
        <h1>Comunidade</h1>
        <p>Descubra o que outras pessoas estão avaliando, escrevendo e compartilhando.</p>
      </header>
      <Suspense fallback={<p className={styles.mensagem}>Carregando comunidade...</p>}>
        <ConteudoComunidade />
      </Suspense>
    </main>
  );
}