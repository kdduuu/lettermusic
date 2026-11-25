import Link from "next/link";
import { Suspense } from "react";
import { CapaAlbum } from "@/components/capa-album";
import { VitrineLista } from "@/components/vitrine-lista";
import { obterCapaAlbum } from "@/lib/catalogo";
import { consultarComunidade, type Atividade, type ObraEmAlta } from "@/lib/comunidade";
import styles from "./page.module.css";

function formatarData(data: string) {
  const partes = /^(\d{4})-(\d{2})-(\d{2})/.exec(data);
  return partes ? `${partes[1]}-${partes[2]}-${partes[3]}` : "";
}
function plural(n: number, singular: string, pluralTexto: string) { return `${n} ${n === 1 ? singular : pluralTexto}`; }
function perfil(username: string) {
  return `/usuarios/${encodeURIComponent(username)}`;
}
function album(id: string) {
  return `/albuns/${encodeURIComponent(id)}`;
}

async function ItemAtividade({ item }: { item: Atividade }) {
  const capa = item.tipo === "lista" ? null : await obterCapaAlbum(item.id_musicbrainz);
  return (
    <li className={styles.atividade}>
      <div className={styles.avatar} aria-hidden="true">{Array.from(item.nome_exibicao.trim())[0]?.toLocaleUpperCase("en-US") || "♪"}</div>
      <article>
        <p className={styles.meta}>
          <Link href={perfil(item.username)}>{item.nome_exibicao}</Link>
          {" · "}<time dateTime={item.criada_em}>{formatarData(item.criada_em)}</time>
        </p>
        {item.tipo === "lista" ? (
          <div className={styles.listaAtividade}>
            <VitrineLista listaId={item.id} titulo={item.titulo} compacta />
            <div>
              <p>Published a list</p>
              <h3><Link href={"/listas/" + item.id}>{item.titulo}</Link></h3>
            </div>
          </div>
        ) : (
          <div className={styles.atividadeMusical}>
            <Link href={album(item.id_musicbrainz)} aria-label={"Open album " + item.titulo}>
              <CapaAlbum url={capa} titulo={item.titulo} className={styles.capaFeed} />
            </Link>
            <div>
              <p className={styles.acaoTexto}>{item.tipo === "review" ? "Reviewed" : "Rated"}</p>
              <h3><Link href={album(item.id_musicbrainz)}>{item.titulo}</Link></h3>
              {item.artista ? <p className={styles.meta}>{item.artista}</p> : null}
              {item.tipo === "review" ? (
                <p className={styles.resumo}>{item.texto}</p>
              ) : <p className={styles.nota}>★ {item.nota.toLocaleString("en-US", { maximumFractionDigits: 1 })}/5</p>}
            </div>
          </div>
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
          <div><strong>{obra.titulo}</strong><p>{obra.artista ?? "Unknown artist"}</p></div>
        </Link>
        
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
        <h2 id="atividades">Recent activity</h2>
        {dados.atividades.length ? <ul className={styles.atividades}>
          {dados.atividades.map((item) => <ItemAtividade key={`${item.tipo}-${item.id}`} item={item} />)}
        </ul> : <p className={styles.mensagem}>No public activity yet.</p>}
        
      </section>
      <aside className={styles.lateral} aria-label="Community highlights">
        <section aria-labelledby="membros">
          <h2 id="membros">Active members</h2>
          
          {dados.membros_ativos.length ? <ul className={styles.membros}>
            {dados.membros_ativos.map((membro) => (
              <li key={membro.username} className={styles.membro}>
                <span className={styles.avatarMembro} aria-hidden="true">{Array.from(membro.nome_exibicao.trim())[0]?.toLocaleUpperCase("en-US") || "♪"}</span>
                <div>
                  <Link href={perfil(membro.username)}>{membro.nome_exibicao}</Link>
                  <p className={styles.meta}>@{membro.username} · {plural(membro.contribuicoes, "contribution", "contributions")}</p>
                </div>
              </li>
            ))}
          </ul> : <p className={styles.mensagem}>No contributions yet.</p>}
        </section>
        <section aria-labelledby="em-alta">
          <h2 id="em-alta">Trending</h2>
          
          {dados.em_alta.length ? <Suspense fallback={<p className={styles.mensagem}>Loading covers…</p>}><EmAlta obras={dados.em_alta} /></Suspense> : <p className={styles.mensagem}>Nothing trending yet.</p>}
        </section>
      </aside>
    </div>
  );
}

export default function ComunidadePage() {
  return (
    <main className={styles.container}>
      <header className={styles.cabecalho}>
        <div>
          
          <h1>Community</h1>
        </div>
        
      </header>
      <Suspense fallback={<p className={styles.mensagem}>Loading community…</p>}>
        <ConteudoComunidade />
      </Suspense>
    </main>
  );
}