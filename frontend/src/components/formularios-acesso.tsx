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
      <label htmlFor="identificador">Username or email</label>
      <input id="identificador" name="identificador" autoComplete="username" required maxLength={254} />
      <label htmlFor="senha-login">Password</label>
      <input id="senha-login" name="senha" type="password" autoComplete="current-password" required />
      <p className={styles.alternativa}>
        <Link href="/esqueci-senha">Forgot password?</Link>
      </p>
      {estado.mensagem && <p role="alert" className={styles.mensagem}>{estado.mensagem}</p>}
      <button type="submit" disabled={pendente}>{pendente ? "Signing in…" : "Sign in"}</button>
      <p className={styles.alternativa}>Don't have an account? <Link href="/cadastro">Sign up</Link></p>
      <p className={styles.alternativa}>Didn't receive a confirmation email? <Link href="/reenviar-confirmacao">Resend link</Link></p>
    </form>
  );
}

export function FormularioCadastro() {
  const [estado, acao, pendente] = useActionState(cadastrar, ESTADO_INICIAL);

  return (
    <form action={acao} className={styles.form}>
      <label htmlFor="username">Username</label>
      <input id="username" name="username" autoComplete="username" minLength={3} maxLength={30} pattern="[A-Za-z0-9_]+" required />
      <label htmlFor="nome_exibicao">Display name</label>
      <input id="nome_exibicao" name="nome_exibicao" autoComplete="name" minLength={2} maxLength={80} required />
      <label htmlFor="email">Email</label>
      <input id="email" name="email" type="email" autoComplete="email" maxLength={254} required />
      <label htmlFor="senha-cadastro">Password (at least 12 characters)</label>
      <input id="senha-cadastro" name="senha" type="password" autoComplete="new-password" minLength={12} maxLength={128} required />
      {estado.mensagem && <p role="alert" className={styles.mensagem}>{estado.mensagem}</p>}
      <button type="submit" disabled={pendente}>{pendente ? "Creating account…" : "Sign up"}</button>
      <p className={styles.alternativa}>Already have an account? <Link href="/entrar">Sign in</Link></p>
    </form>
  );
}