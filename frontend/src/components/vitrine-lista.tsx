import styles from "./vitrine-lista.module.css";

type Props = {
  listaId: number;
  titulo?: string;
  token?: string | null;
  compacta?: boolean;
};

function ArteDaLista({ listaId, titulo = "Coleção musical", ampla = false, compacta = false }: Props & { ampla?: boolean }) {
  const tom = "grafite";
  return (
    <div
      role="img"
      aria-label={"Capa ilustrada da lista " + titulo}
      className={[styles.arte, styles[tom], ampla ? styles.ampla : compacta ? styles.compacta : styles.miniatura].join(" ")}
    >
      <span className={styles.marca} aria-hidden="true">LM.</span>
      <span className={styles.forma} aria-hidden="true" />
      <span className={styles.anel} aria-hidden="true" />
      <span className={styles.risco} aria-hidden="true" />
      <span className={styles.edicao} aria-hidden="true">
        <span>COLLECTION</span>
        <span>{String(listaId).padStart(3, "0")}</span>
      </span>
    </div>
  );
}

// As listas têm identidade própria; as capas dos álbuns permanecem dentro da coleção.
export function VitrineLista({ listaId, titulo, compacta = false }: Props) {
  return <ArteDaLista listaId={listaId} titulo={titulo} compacta={compacta} />;
}

export function ColagemEditorialLista({ listaId, titulo }: Props) {
  return <ArteDaLista listaId={listaId} titulo={titulo} ampla />;
}
