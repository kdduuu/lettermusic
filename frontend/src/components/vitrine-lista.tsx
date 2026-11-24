import styles from "./vitrine-lista.module.css";

type Props = {
  listaId: number;
  titulo?: string;
  token?: string | null;
  compacta?: boolean;
};

function ArteDaLista({ titulo, ampla = false, compacta = false }: { titulo?: string; ampla?: boolean; compacta?: boolean }) {
  return (
    <div
      role="img"
      aria-label={"Capa da lista " + (titulo ?? "musical")}
      className={[styles.arte, ampla ? styles.ampla : compacta ? styles.compacta : styles.miniatura].join(" ")}
    >
      <span className={styles.marca} aria-hidden="true">LM.</span>
    </div>
  );
}

// Identidade neutra; as capas dos álbuns permanecem dentro da lista.
export function VitrineLista({ titulo, compacta = false }: Props) {
  return <ArteDaLista titulo={titulo} compacta={compacta} />;
}

export function ColagemEditorialLista({ titulo }: Props) {
  return <ArteDaLista titulo={titulo} ampla />;
}
