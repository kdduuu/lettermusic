import Link from "next/link";
import { Suspense } from "react";
import { notFound } from "next/navigation";
import { Paginacao, ResultadosMusicais } from "@/components/exploracao-musical";
import { artista, discografia, obterPagina } from "@/lib/exploracao";
import { MBID_VALIDO } from "@/lib/estado-album";
import styles from "../../page.module.css";
import controles from "@/components/controles.module.css";
import { CapaArtista } from "@/components/capa-artista";
import visual from "./page.module.css";

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

  const obras = await discografia(id, pagina, tipo);
  const itens = obras.ok ? [...obras.dados.resultados] : [];

  if (ordem !== "catalogo") {
    itens.sort((a, b) => {
      if (!a.data && !b.data) return a.titulo.localeCompare(b.titulo);
      if (!a.data) return 1;
      if (!b.data) return -1;
      return ordem === "antigos"
        ? a.data.localeCompare(b.data)
        : b.data.localeCompare(a.data);
    });
  }

  return (
    <>
      <section className={visual.artistaHero}>
        <CapaArtista nome={perfil.dados.titulo} id={id} tamanho="grande" />
        <div className={visual.identidade}>
          <h1>{perfil.dados.titulo}</h1>
          <p>{[perfil.dados.tipo, perfil.dados.subtitulo].filter(Boolean).join(" · ")}</p>
        </div>
      </section>

      <section className={visual.discografia}>
        <h2>Discografia</h2>
        
        <form action={`/artistas/${id}`} className={controles.linha}>
          <div className={controles.grupo}>
          <label htmlFor="tipo-discografia">Lançamentos</label>
          <select className={controles.selecao} id="tipo-discografia" name="tipo" defaultValue={tipo}>
            <option value="todos">Todos</option>
            <option value="album">Álbuns</option>
            <option value="single">Singles</option>
            <option value="ep">EPs</option>
            <option value="compilation">Coletâneas</option>
            <option value="live">Ao vivo</option>
          </select>
          </div>
          <div className={controles.grupo}>
          <label htmlFor="ordem-discografia">Ordem</label>
          <select className={controles.selecao} id="ordem-discografia" name="ordem" defaultValue={ordem}>
            <option value="catalogo">Catálogo</option>
            <option value="antigos">Mais antigos</option>
            <option value="recentes">Mais recentes</option>
          </select>
          </div>
          <button className={controles.primario} type="submit">Aplicar</button>
        </form>
        {obras.ok ? (
          <>
            <ResultadosMusicais itens={itens} categoria="albuns" apresentacao="galeria" />
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
      <Link href="/" className={visual.voltar}>Descobrir</Link>
      <Suspense fallback={<p className={styles.message}>Carregando artista...</p>}>
        <Conteudo {...props} />
      </Suspense>
    </main>
  );
}
