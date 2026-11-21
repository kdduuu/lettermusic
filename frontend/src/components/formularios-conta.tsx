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
          "Excluir sua conta e todos os seus registros? Esta ação é permanente."
        )) {
          evento.preventDefault();
        }
      }}
    >
      <label htmlFor="exclusao_senha">
        Confirme sua senha
      </label>
      <input
        id="exclusao_senha"
        name="senha_atual"
        type="password"
        autoComplete="current-password"
        required
      />

      <label htmlFor="confirmacao_exclusao">
        Digite EXCLUIR para confirmar
      </label>
      <input
        id="confirmacao_exclusao"
        name="confirmacao_exclusao"
        autoComplete="off"
        pattern="EXCLUIR"
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
        {pendente ? "Excluindo..." : "Excluir minha conta"}
      </button>
    </form>
  );
}
