import { Suspense } from "react";
import type { Metadata } from "next";
import { FormularioRedefinicao } from "@/components/formularios-recuperacao";
import styles from "../autenticacao.module.css";

export const metadata: Metadata = {
  title: "Reset password | Lettermusic",
  referrer: "no-referrer",
  robots: { index: false, follow: false },
};

export default function RedefinirSenhaPage() {
  return (
    <main className={styles.container}>
      <h1>New password</h1>
      <p className={styles.introducao}>
        Choose a new password.
      </p>
      <Suspense fallback={<p>Loading form…</p>}>
        <FormularioRedefinicao />
      </Suspense>
    </main>
  );
}
