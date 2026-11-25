import Link from "next/link";
import { Suspense } from "react";
import { notFound } from "next/navigation";
import { Paginacao, ResultadosMusicais } from "@/components/exploracao-musical";
import { artista, discografia, obterPagina, type Item } from "@/lib/exploracao";
import { MBID_VALIDO } from "@/lib/estado-album";
import styles from "../../page.module.css";
import controles from "@/components/controles.module.css";
import { CapaArtista } from "@/components/capa-artista";
import { tipoMusicalEmPortugues } from "@/lib/visual-metadados";
import visual from "./page.module.css";

const categories = [
  { key:"studio", label:"Studio albums" },
  { key:"ep", label:"EPs" },
  { key:"single", label:"Singles" },
  { key:"compilation", label:"Compilations" },
  { key:"live", label:"Live albums" },
  { key:"other", label:"Other releases" },
] as const;
function category(item:Item):typeof categories[number]["key"] {
  const primary=item.tipo?.toLowerCase();
  const secondary=(item.subtitulo??"").toLowerCase().split(" · ");
  if (primary==="live" || secondary.includes("live")) return "live";
  if (primary==="compilation" || secondary.includes("compilation")) return "compilation";
  if (primary==="album" && !secondary.some(Boolean)) return "studio";
  if (primary==="ep") return "ep";
  if (primary==="single") return "single";
  return "other";
}
type Props = {
  params: Promise<{ id: string }>;
  searchParams: Promise<{
    pagina?: string | string[];
    tipo?: string | string[];
    ordem?: string | string[];
  }>;
};

async function Conteudo({ params, searchParams }: Props) {
  const { id } = await params;
  if (!MBID_VALIDO.test(id)) notFound();

  const filtros = await searchParams;
  const pagina = obterPagina(filtros.pagina);
  const tipos = ["todos", "album", "single", "ep", "compilation", "live"];
  const tipo = typeof filtros.tipo === "string" && tipos.includes(filtros.tipo) ? filtros.tipo : "todos";
  const ordem = filtros.ordem === "antigos" || filtros.ordem === "recentes" ? filtros.ordem : "catalogo";
  const endereco = `/artistas/${id}?${new URLSearchParams({ tipo, ordem })}`;
  const perfil = await artista(id);
  if (!perfil.ok) return <p role="alert" className={styles.message}>{perfil.mensagem}</p>;

  const obras = await discografia(id, pagina, tipo, ordem);
  const itens = obras.ok ? obras.dados.resultados : [];

  return (
    <>
      <section className={visual.artistaHero}>
        <CapaArtista nome={perfil.dados.titulo} id={id} tamanho="grande" />
        <div className={visual.identidade}>
          <h1>{perfil.dados.titulo}</h1>
          <p>{[tipoMusicalEmPortugues(perfil.dados.tipo), perfil.dados.subtitulo].filter(Boolean).join(" · ")}</p>
        </div>
      </section>

      <section className={visual.discografia}>
        <h2>Discography</h2>
        
        <nav className={visual.releaseTabs} aria-label="Release types">
          {([{key:"todos",label:"All"},{key:"album",label:"Albums"},{key:"single",label:"Singles"},{key:"ep",label:"EPs"},{key:"compilation",label:"Compilations"},{key:"live",label:"Live"}]).map(tab=><Link prefetch={false} key={tab.key} href={`/artistas/${id}?tipo=${tab.key}&ordem=${ordem}`} aria-current={tipo===tab.key?"page":undefined}>{tab.label}</Link>)}
        </nav>
        <form action={`/artistas/${id}`} className={visual.sort}>
          <input type="hidden" name="tipo" value={tipo}/>
          <label htmlFor="ordem-discografia">Sort by</label>
          <select className={controles.selecao} id="ordem-discografia" name="ordem" defaultValue={ordem}>
            <option value="catalogo">Catalog order</option><option value="antigos">Oldest first</option><option value="recentes">Newest first</option>
          </select>
          <button className={visual.sortButton} type="submit" title="Apply sort" aria-label="Apply sort">↵</button>
        </form>
        {obras.ok ? (
          <>
            {itens.length ? categories.map(group=>{
              const records=itens.filter(item=>category(item)===group.key);
              return records.length?<section key={group.key} className={visual.releaseGroup}><h3>{group.label}</h3><ResultadosMusicais itens={records} categoria="albuns" apresentacao="galeria"/></section>:null;
            }):<p className={styles.message}>No releases found.</p>}
            <Paginacao pagina={pagina} temProxima={obras.dados.tem_proxima} endereco={endereco} />
          </>
        ) : <p role="alert" className={styles.message}>{obras.mensagem}</p>}
      </section>
    </>
  );
}

export default function ArtistaPage(props: Props) {
  return (
    <main className={styles.container}>
      <Link href="/buscar" className={visual.voltar}>← Search</Link>
      <Suspense fallback={<p className={styles.message}>Loading artist…</p>}>
        <Conteudo {...props} />
      </Suspense>
    </main>
  );
}
