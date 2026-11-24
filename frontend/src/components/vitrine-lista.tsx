import styles from "./vitrine-lista.module.css";

type Props = {
  listaId: number;
  titulo?: string;
  token?: string | null;
};

function ArteDaLista({ listaId, titulo = "Coleção musical", ampla = false }: Props & { ampla?: boolean }) {
  const tom = ["grafite", "azul", "oliva", "ameixa", "areia"][listaId % 5];
  return (
    <div
      role="img"
      aria-label={"Capa ilustrada da lista " + titulo}
      className={[styles.arte, styles[tom], ampla ? styles.ampla : styles.miniatura].join(" ")}
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
export function VitrineLista({ listaId, titulo }: Props) {
  return <ArteDaLista listaId={listaId} titulo={titulo} />;
}

export function ColagemEditorialLista({ listaId, titulo }: Props) {
  return <ArteDaLista listaId={listaId} titulo={titulo} ampla />;
}
