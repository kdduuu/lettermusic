import { CapaAlbum } from "@/components/capa-album";
import { obterCapaAlbum } from "@/lib/catalogo";
import { detalheLista } from "@/lib/listas";
import styles from "./vitrine-lista.module.css";

// Somente leitura: a API decide a privacidade, sem salvar nem alterar álbuns.
export async function VitrineLista({
  listaId, token,
}: {
  listaId: number;
  token?: string | null;
}) {
  const resultado = await detalheLista(listaId, token ?? null, 1);
  const itens = resultado.ok ? resultado.dados.destaques.slice(0, 4) : [];
  const capas = await Promise.all(itens.map(item =>
    item.id_musicbrainz ? obterCapaAlbum(item.id_musicbrainz) : Promise.resolve(null)
  ));
  return (
    <div className={styles.colagem} aria-hidden="true">
      {Array.from({ length: 4 }, (_, indice) => {
        const item = itens[indice];
        if (!item) return <div className={styles.vazio} key={indice}>♪</div>;
        return <CapaAlbum
          key={item.id}
          className={styles.capa}
          url={capas[indice]}
          titulo={item.titulo ?? "Álbum"}
        />;
      })}
    </div>
  );
}
