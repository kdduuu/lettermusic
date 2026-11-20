import { FormularioEsqueci } from "@/components/formularios-recuperacao";
import styles from "../autenticacao.module.css";

export default function EsqueciSenhaPage() {
  return (
    <main className={styles.container}>
      <h1>Recuperar senha</h1>
      <p className={styles.introducao}>
        Informe seu e-mail para receber um link de recuperação.
      </p>
      <FormularioEsqueci />
    </main>
  );
}
