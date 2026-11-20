"use client";

import { useActionState } from "react";
import { atualizarNome, atualizarSenha } from "@/app/acoes-conta";
import { ESTADO_INICIAL } from "@/lib/estado-acoes";
import styles from "@/app/autenticacao.module.css";

export function FormularioNome({ nome }: { nome: string }) {
  const [estado, acao, pendente] = useActionState(
    atualizarNome, ESTADO_INICIAL
  );

  return (
    <form action={acao} className={styles.form}>
      <label htmlFor="nome_exibicao">Nome de exibição</label>
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
        {pendente ? "Salvando..." : "Salvar nome"}
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
      <label htmlFor="senha_atual">Senha atual</label>
      <input
        id="senha_atual" name="senha_atual"
        type="password" autoComplete="current-password" required
      />

      <label htmlFor="senha_nova">Nova senha</label>
      <input
        id="senha_nova" name="senha_nova"
        type="password" minLength={12} maxLength={128}
        autoComplete="new-password" required
      />

      <label htmlFor="confirmacao">Confirmar nova senha</label>
      <input
        id="confirmacao" name="confirmacao"
        type="password" minLength={12} maxLength={128}
        autoComplete="new-password" required
      />

      {estado.mensagem && (
        <p role="alert" className={styles.mensagem}>{estado.mensagem}</p>
      )}
      <button disabled={pendente}>
        {pendente ? "Alterando..." : "Alterar senha"}
      </button>
    </form>
  );
}
