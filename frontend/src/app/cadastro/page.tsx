import { FormularioCadastro } from "@/components/formularios-acesso";
import styles from "../autenticacao.module.css";

export default function CadastroPage() {
  return (
    <main className={styles.container}>
      <h1>Criar conta</h1>
      <p className={styles.introducao}>Registre suas descobertas e organize sua música.</p>
      <FormularioCadastro />
    </main>
  );
}