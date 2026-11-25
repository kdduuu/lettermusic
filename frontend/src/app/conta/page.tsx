
import { Suspense } from "react";
import { redirect } from "next/navigation";
import { requisitarBackend } from "@/lib/backend";
import { obterTokenSessao } from "@/lib/sessao";
import {
  FormularioNome,
  FormularioSenha,
  FormularioExcluirConta,
} from "@/components/formularios-conta";
import { FormularioReenviar } from "@/components/formularios-recuperacao";
import styles from "../autenticacao.module.css";

type Conta = {
  username: string;
  nome_exibicao: string;
  email: string;
  email_confirmado: boolean;
};

function contaValida(valor: unknown): valor is Conta {
  if (!valor || typeof valor !== "object") return false;

  const dados = valor as Record<string, unknown>;

  return typeof dados.username === "string" &&
    typeof dados.nome_exibicao === "string" &&
    typeof dados.email === "string" &&
    typeof dados.email_confirmado === "boolean";
}

// Conteudo dinamico: depende da sessao do usuario.
async function ConteudoConta() {
  const token = await obterTokenSessao();
  if (!token) redirect("/entrar");

  let conta: Conta | null = null;
  let expirou = false;

  try {
    const resposta = await requisitarBackend("/auth/conta", {
      headers: { Authorization: `Bearer ${token}` },
    });

    if (resposta.status === 401) {
      expirou = true;
    } else if (resposta.ok) {
      const dados: unknown = await resposta.json();
      if (contaValida(dados)) conta = dados;
    }
  } catch {
    // Falha temporaria da API, sem expor dados pessoais.
  }

  if (expirou) redirect("/entrar");

  if (!conta) {
    return (
      <main className={styles.container}>
        <h1>Account</h1>
        <p role="alert">
          Unable to load your account.
        </p>
      </main>
    );
  }

  return (
    <main className={styles.container}>
      <h1>Account</h1>


      <section>
        <h2>Personal details</h2>
        <p>Username: <strong>@{conta.username}</strong></p>
        <p>Email: <strong>{conta.email}</strong></p>
        <p>
          Status: {conta.email_confirmado ? "Confirmed" : "Unconfirmed"}
        </p>
        {!conta.email_confirmado && (
          <FormularioReenviar emailInicial={conta.email} />
        )}
        <FormularioNome nome={conta.nome_exibicao} />
      </section>

      <section style={{ marginTop: 48 }}>
        <h2>Security</h2>
        <p className={styles.introducao}>
          Changing your password will sign you out of all sessions.
          Sign in again with your new password.
        </p>
        <FormularioSenha />
      </section>

      <section style={{ marginTop: 48 }}>
        <h2>Delete account</h2>
        <p className={styles.introducao}>
          This is permanent. Your profile, lists, ratings,
          reviews and personal activity will be deleted.
        </p>
        <FormularioExcluirConta />
      </section>
    </main>
  );
}

// Estrutura estatica + conteudo dinamico sob Suspense.
export default function ContaPage() {
  return (
    <Suspense
      fallback={
        <main className={styles.container}>
          <h1>Account</h1>
          <p className={styles.introducao}>
            Loading account…
          </p>
        </main>
      }
    >
      <ConteudoConta />
    </Suspense>
  );
}
