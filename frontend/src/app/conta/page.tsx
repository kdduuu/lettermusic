
import { Suspense } from "react";
import { redirect } from "next/navigation";
import { requisitarBackend } from "@/lib/backend";
import { obterTokenSessao } from "@/lib/sessao";
import {
  FormularioNome,
  FormularioSenha,
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
        <h1>Minha conta</h1>
        <p role="alert">
          Não foi possível carregar sua conta agora.
        </p>
      </main>
    );
  }

  return (
    <main className={styles.container}>
      <h1>Minha conta</h1>
      <p className={styles.introducao}>
        Dados pessoais e segurança do seu perfil.
      </p>

      <section>
        <h2>Dados pessoais</h2>
        <p>Usuário: <strong>@{conta.username}</strong></p>
        <p>E-mail: <strong>{conta.email}</strong></p>
        <p>
          Status: {conta.email_confirmado ? "Confirmado" : "Pendente de confirmação"}
        </p>
        {!conta.email_confirmado && (
          <FormularioReenviar emailInicial={conta.email} />
        )}
        <FormularioNome nome={conta.nome_exibicao} />
      </section>

      <section style={{ marginTop: 48 }}>
        <h2>Segurança</h2>
        <p className={styles.introducao}>
          Ao alterar a senha, suas sessões serão encerradas.
          Entre novamente com a nova senha.
        </p>
        <FormularioSenha />
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
          <h1>Minha conta</h1>
          <p className={styles.introducao}>
            Carregando informações da conta...
          </p>
        </main>
      }
    >
      <ConteudoConta />
    </Suspense>
  );
}
