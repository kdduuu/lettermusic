"use client";

import Link from "next/link";
import { useActionState } from "react";
import { cadastrar, entrar } from "@/app/acoes";
import { ESTADO_INICIAL } from "@/lib/estado-acoes";
import styles from "@/app/autenticacao.module.css";

export function FormularioLogin() {
  const [estado, acao, pendente] = useActionState(entrar, ESTADO_INICIAL);

  return (
    <form action={acao} className={styles.form}>
      <label htmlFor="identificador">Usuário ou e-mail</label>
      <input id="identificador" name="identificador" autoComplete="username" required maxLength={254} />
      <label htmlFor="senha-login">Senha</label>
      <input id="senha-login" name="senha" type="password" autoComplete="current-password" required />
      <p className={styles.alternativa}>
        <Link href="/esqueci-senha">Esqueci minha senha</Link>
      </p>
      {estado.mensagem && <p role="alert" className={styles.mensagem}>{estado.mensagem}</p>}
      <button type="submit" disabled={pendente}>{pendente ? "Entrando..." : "Entrar"}</button>
      <p className={styles.alternativa}>Ainda não tem conta? <Link href="/cadastro">Criar conta</Link></p>
      <p className={styles.alternativa}>Não recebeu a confirmação? <Link href="/reenviar-confirmacao">Reenviar link</Link></p>
    </form>
  );
}

export function FormularioCadastro() {
  const [estado, acao, pendente] = useActionState(cadastrar, ESTADO_INICIAL);

  return (
    <form action={acao} className={styles.form}>
      <label htmlFor="username">Nome de usuário</label>
      <input id="username" name="username" autoComplete="username" minLength={3} maxLength={30} pattern="[A-Za-z0-9_]+" required />
      <label htmlFor="nome_exibicao">Nome de exibição</label>
      <input id="nome_exibicao" name="nome_exibicao" autoComplete="name" minLength={2} maxLength={80} required />
      <label htmlFor="email">E-mail</label>
      <input id="email" name="email" type="email" autoComplete="email" maxLength={254} required />
      <label htmlFor="senha-cadastro">Senha (mínimo de 12 caracteres)</label>
      <input id="senha-cadastro" name="senha" type="password" autoComplete="new-password" minLength={12} maxLength={128} required />
      {estado.mensagem && <p role="alert" className={styles.mensagem}>{estado.mensagem}</p>}
      <button type="submit" disabled={pendente}>{pendente ? "Criando conta..." : "Criar conta"}</button>
      <p className={styles.alternativa}>Já tem conta? <Link href="/entrar">Entrar</Link></p>
    </form>
  );
}