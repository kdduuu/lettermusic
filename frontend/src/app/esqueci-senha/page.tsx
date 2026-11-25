import { FormularioEsqueci } from "@/components/formularios-recuperacao";
import styles from "../autenticacao.module.css";

export default function EsqueciSenhaPage() {
  return (
    <main className={styles.container}>
      <h1>Reset password</h1>
      <p className={styles.introducao}>
        Enter your email address to receive a reset link.
      </p>
      <FormularioEsqueci />
    </main>
  );
}
