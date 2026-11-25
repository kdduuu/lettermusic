"use client";

import { useActionState } from "react";
import { atualizarNome, atualizarSenha, excluirConta } from "@/app/acoes-conta";
import { ESTADO_INICIAL } from "@/lib/estado-acoes";
import styles from "@/app/autenticacao.module.css";

export function FormularioNome({ nome }: { nome: string }) {
  const [estado, acao, pendente] = useActionState(
    atualizarNome, ESTADO_INICIAL
  );

  return (
    <form action={acao} className={styles.form}>
      <label htmlFor="nome_exibicao">Display name</label>
      <input
        id="nome_exibicao"
        name="nome_exibicao"
        defaultValue={nome}
        minLength={2}
        maxLength={80}
        required
      />
      {estado.mensagem && (
        <p role="status" className={styles.mensagem}>{estado.mensagem}</p>
      )}
      <button disabled={pendente}>
        {pendente ? "Saving…" : "Save name"}
      </button>
    </form>
  );
}

export function FormularioSenha() {
  const [estado, acao, pendente] = useActionState(
    atualizarSenha, ESTADO_INICIAL
  );

  return (
    <form action={acao} className={styles.form}>
      <label htmlFor="senha_atual">Current password</label>
      <input
        id="senha_atual" name="senha_atual"
        type="password" autoComplete="current-password" required
      />

      <label htmlFor="senha_nova">New password</label>
      <input
        id="senha_nova" name="senha_nova"
        type="password" minLength={12} maxLength={128}
        autoComplete="new-password" required
      />

      <label htmlFor="confirmacao">Confirm new password</label>
      <input
        id="confirmacao" name="confirmacao"
        type="password" minLength={12} maxLength={128}
        autoComplete="new-password" required
      />

      {estado.mensagem && (
        <p role="alert" className={styles.mensagem}>{estado.mensagem}</p>
      )}
      <button disabled={pendente}>
        {pendente ? "Updating…" : "Change password"}
      </button>
    </form>
  );
}

export function FormularioExcluirConta() {
  const [estado, acao, pendente] = useActionState(
    excluirConta, ESTADO_INICIAL
  );

  return (
    <form
      action={acao}
      className={styles.form}
      onSubmit={(evento) => {
        if (!window.confirm(
          "Delete your account and all your records? This cannot be undone."
        )) {
          evento.preventDefault();
        }
      }}
    >
      <label htmlFor="exclusao_senha">
        Confirm password
      </label>
      <input
        id="exclusao_senha"
        name="senha_atual"
        type="password"
        autoComplete="current-password"
        required
      />

      <label htmlFor="confirmacao_exclusao">
        Type DELETE to confirm
      </label>
      <input
        id="confirmacao_exclusao"
        name="confirmacao_exclusao"
        autoComplete="off"
        pattern="DELETE"
        required
      />

      {estado.mensagem && (
        <p role="alert" className={styles.mensagem}>
          {estado.mensagem}
        </p>
      )}

      <button
        type="submit"
        disabled={pendente}
      >
        {pendente ? "Deleting…" : "Delete my account"}
      </button>
    </form>
  );
}
