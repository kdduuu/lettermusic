import styles from "./vitrine-lista.module.css";

type Props = {
  listaId: number;
  titulo?: string;
  token?: string | null;
  compacta?: boolean;
};

function ArteDaLista({ listaId, titulo, ampla = false, compacta = false }: Props & { ampla?: boolean }) {
  return (
    <div role="img" aria-label={"Cover for list " + (titulo ?? "music")}
      data-edition={String(Math.abs(listaId) % 4)}
      className={[styles.arte, ampla ? styles.ampla : compacta ? styles.compacta : styles.miniatura].join(" ")}>
      
        <span className={styles.rodape} aria-hidden="true">
          <span>COLLECTION</span><span>{String(listaId).padStart(3, "0")}</span>
        </span>
    </div>
  );
}

export function VitrineLista(props: Props) {
  return <ArteDaLista {...props} />;
}

export function ColagemEditorialLista(props: Props) {
  return <ArteDaLista {...props} ampla />;
}
