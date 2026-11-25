import { Suspense } from "react";
import type { Metadata } from "next";
import { FormularioConfirmarEmail } from "@/components/formularios-recuperacao";
import styles from "../autenticacao.module.css";

export const metadata: Metadata = {
  title: "Confirm email | Lettermusic",
  referrer: "no-referrer",
  robots: { index: false, follow: false },
};

export default function ConfirmarEmailPage() {
  return (
    <main className={styles.container}>
      <h1>Confirm email</h1>
      <p className={styles.introducao}>
        Confirm your email address to secure your account.
      </p>
      <Suspense fallback={<p>Loading confirmation…</p>}>
        <FormularioConfirmarEmail />
      </Suspense>
    </main>
  );
}
