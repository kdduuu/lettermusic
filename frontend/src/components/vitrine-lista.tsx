import styles from "./vitrine-lista.module.css";

type Props = {
  listaId: number;
  titulo?: string;
  token?: string | null;
  compacta?: boolean;
};

function ArteDaLista({ listaId, titulo, ampla = false, compacta = false }: Props & { ampla?: boolean }) {
  return (
    <div role="img" aria-label={"Capa da lista " + (titulo ?? "musical")}
      className={[styles.arte, ampla ? styles.ampla : compacta ? styles.compacta : styles.miniatura].join(" ")}>
      <span className={styles.marca} aria-hidden="true">LM.</span>
      {!compacta ? (
        <span className={styles.rodape} aria-hidden="true">
          <span>COLLECTION</span><span>{String(listaId).padStart(3, "0")}</span>
        </span>
      ) : null}
    </div>
  );
}

export function VitrineLista(props: Props) {
  return <ArteDaLista {...props} />;
}

export function ColagemEditorialLista(props: Props) {
  return <ArteDaLista {...props} ampla />;
}
