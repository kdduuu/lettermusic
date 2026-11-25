import { FormularioCadastro } from "@/components/formularios-acesso";
import styles from "../autenticacao.module.css";

export default function CadastroPage() {
  return (
    <main className={styles.container}>
      <h1>Sign up</h1>
      
      <FormularioCadastro />
    </main>
  );
}