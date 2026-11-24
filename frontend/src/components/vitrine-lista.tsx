import Link from "next/link";
import { CapaAlbum } from "@/components/capa-album";
import { obterCapaAlbum } from "@/lib/catalogo";
import { detalheLista, type ItemLista } from "@/lib/listas";
import styles from "./vitrine-lista.module.css";

type Aparencia = "cartao" | "destaque";

function CapaEditorial({
  itens, urls, nomeLista, aparencia,
}: {
  itens: ItemLista[];
  urls: (string | null)[];
  nomeLista: string;
  aparencia: Aparencia;
}) {
  const quantidade = Math.min(itens.length, 4);
  const classeQuantidade = [styles.vazia, styles.uma, styles.duas, styles.tres, styles.quatro][quantidade];
  return (
    <div
      className={[styles.composicao, classeQuantidade, aparencia === "destaque" ? styles.destaque : styles.cartao].join(" ")}
      aria-label={quantidade ? "Capa composta por álbuns da lista " + nomeLista : "Lista sem álbuns: " + nomeLista}
      role="img"
    >
      {quantidade === 0 ? (
        <div className={styles.semItens}>
          <span className={styles.marcaVazia}>LETTERMUSIC / COLEÇÃO</span>
          <strong>{nomeLista}</strong>
          <span className={styles.linhaVazia} aria-hidden="true" />
        </div>
      ) : (
        <>
          {itens.slice(0, 4).map((item, indice) => {
            const capa = urls[indice];
            const titulo = item.titulo ?? "Álbum sem título";
            const conteudo = capa ? (
              <CapaAlbum url={capa} titulo={titulo} className={styles.capa} />
            ) : (
              <div className={styles.capaAusente}>
                <span>ÁLBUM</span><strong>{titulo}</strong>
              </div>
            );
            return aparencia === "destaque" && item.id_musicbrainz ? (
              <Link
                key={item.id}
                className={styles.celula}
                href={"/albuns/" + encodeURIComponent(item.id_musicbrainz)}
                aria-label={"Abrir álbum " + titulo}
              >{conteudo}</Link>
            ) : <div key={item.id} className={styles.celula}>{conteudo}</div>;
          })}
          {quantidade === 1 ? (
            <div className={styles.legendaUnica}>
              <span>01 / 01</span>
              <strong>{itens[0].titulo ?? nomeLista}</strong>
              <small>{itens[0].artista ?? "Uma seleção pessoal"}</small>
            </div>
          ) : null}
        </>
      )}
    </div>
  );
}

export async function ColagemEditorialLista({
  itens, titulo,
}: {
  itens: ItemLista[];
  titulo: string;
}) {
  const selecionados = itens.slice(0, 4);
  const urls = await Promise.all(selecionados.map(item =>
    item.id_musicbrainz ? obterCapaAlbum(item.id_musicbrainz) : Promise.resolve(null)
  ));
  return <CapaEditorial itens={selecionados} urls={urls} nomeLista={titulo} aparencia="destaque" />;
}

// Somente leitura: a API controla a privacidade de cada coleção.
export async function VitrineLista({
  listaId, token, titulo = "Coleção musical",
}: {
  listaId: number;
  token?: string | null;
  titulo?: string;
}) {
  const resultado = await detalheLista(listaId, token ?? null, 1);
  const itens = resultado.ok ? resultado.dados.destaques.slice(0, 4) : [];
  const urls = await Promise.all(itens.map(item =>
    item.id_musicbrainz ? obterCapaAlbum(item.id_musicbrainz) : Promise.resolve(null)
  ));
  return <CapaEditorial itens={itens} urls={urls} nomeLista={titulo} aparencia="cartao" />;
}
