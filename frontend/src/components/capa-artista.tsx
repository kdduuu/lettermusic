
import { monogramaArtista, variacaoArtista } from "@/lib/visual-artista";
import styles from "./capa-artista.module.css";

export function CapaArtista({
  nome, id, tamanho = "mini",
}: {
  nome: string;
  id: string;
  tamanho?: "mini" | "grande";
}) {
  return (
    <div className={styles.capa + " " + styles[tamanho]} data-variacao={variacaoArtista(id)} aria-hidden="true">
      <span className={styles.monograma}>{monogramaArtista(nome)}</span>
    </div>
  );
}
