import { Suspense } from "react";
import type { Metadata } from "next";
import { FormularioConfirmarEmail } from "@/components/formularios-recuperacao";
import styles from "../autenticacao.module.css";

export const metadata: Metadata = {
  title: "Confirmar e-mail | Lettermusic",
  referrer: "no-referrer",
  robots: { index: false, follow: false },
};

export default function ConfirmarEmailPage() {
  return (
    <main className={styles.container}>
      <h1>Confirmar e-mail</h1>
      <p className={styles.introducao}>
        Confirme seu endereço para proteger sua conta.
      </p>
      <Suspense fallback={<p>Carregando confirmação...</p>}>
        <FormularioConfirmarEmail />
      </Suspense>
    </main>
  );
}
