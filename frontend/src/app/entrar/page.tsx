import { FormularioLogin } from "@/components/formularios-acesso";
import styles from "../autenticacao.module.css";

export default function EntrarPage() {
  return (
    <main className={styles.container}>
      <h1>Entrar</h1>
      <p className={styles.introducao}>Acesse sua biblioteca musical.</p>
      <FormularioLogin />
    </main>
  );
}