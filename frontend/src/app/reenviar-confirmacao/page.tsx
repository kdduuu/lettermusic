import Link from "next/link";
import { FormularioReenviar } from "@/components/formularios-recuperacao";
import styles from "../autenticacao.module.css";

export default function ReenviarConfirmacaoPage() {
  return (
    <main className={styles.container}>
      <h1>Confirmar e-mail</h1>
      <p className={styles.introducao}>
        Não recebeu a mensagem? Solicite outro link.
      </p>
      <FormularioReenviar />
      <p className={styles.alternativa}>
        <Link href="/entrar">Voltar para o login</Link>
      </p>
    </main>
  );
}
