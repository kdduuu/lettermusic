import Link from "next/link";
import { FormularioReenviar } from "@/components/formularios-recuperacao";
import styles from "../autenticacao.module.css";

export default function ReenviarConfirmacaoPage() {
  return (
    <main className={styles.container}>
      <h1>Confirm email</h1>
      <p className={styles.introducao}>
        Didn't receive the email? Request another link.
      </p>
      <FormularioReenviar />
      <p className={styles.alternativa}>
        <Link href="/entrar">Back to sign in</Link>
      </p>
    </main>
  );
}
