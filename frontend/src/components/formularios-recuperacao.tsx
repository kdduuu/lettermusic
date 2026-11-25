"use client";

import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { useActionState } from "react";
import {
  solicitarRecuperacao,
  solicitarConfirmacao,
  redefinirSenha,
  confirmarEmail,
} from "@/app/acoes-recuperacao";
import { ESTADO_INICIAL } from "@/lib/estado-acoes";
import styles from "@/app/autenticacao.module.css";

const TOKEN_VALIDO = /^[A-Za-z0-9_-]{43}$/;

function Resultado({ sucesso, mensagem }: {
  sucesso: boolean;
  mensagem: string;
}) {
  if (!mensagem) return null;

  return (
    <p
      role="status"
      className={sucesso ? styles.sucesso : styles.mensagem}
    >
      {mensagem}
    </p>
  );
}

export function FormularioEsqueci() {
  const [estado, acao, pendente] = useActionState(
    solicitarRecuperacao, ESTADO_INICIAL
  );

  return (
    <form action={acao} className={styles.form}>
      <label htmlFor="email-recuperacao">Email address</label>
      <input
        id="email-recuperacao" name="email" type="email"
        autoComplete="email" maxLength={254} required
      />
      <Resultado {...estado} />
      <button type="submit" disabled={pendente}>
        {pendente ? "Sending…" : "Send reset link"}
      </button>
      <p className={styles.alternativa}>
        <Link href="/entrar">Back to sign in</Link>
      </p>
    </form>
  );
}

export function FormularioReenviar({
  emailInicial = "",
}: { emailInicial?: string }) {
  const [estado, acao, pendente] = useActionState(
    solicitarConfirmacao, ESTADO_INICIAL
  );

  return (
    <form action={acao} className={styles.form}>
      <label htmlFor="email-confirmacao">Email address</label>
      <input
        id="email-confirmacao" name="email" type="email"
        defaultValue={emailInicial}
        autoComplete="email" maxLength={254} required
      />
      <Resultado {...estado} />
      <button type="submit" disabled={pendente}>
        {pendente ? "Sending…" : "Resend confirmation"}
      </button>
    </form>
  );
}

export function FormularioRedefinicao() {
  const parametros = useSearchParams();
  const token = parametros.get("token") ?? "";
  const [estado, acao, pendente] = useActionState(
    redefinirSenha, ESTADO_INICIAL
  );

  if (!TOKEN_VALIDO.test(token)) {
    return (
      <p role="alert" className={styles.mensagem}>
        Invalid link.{" "}
        <Link href="/esqueci-senha">Request another link</Link>
      </p>
    );
  }

  if (estado.sucesso) {
    return (
      <>
        <Resultado {...estado} />
        <p className={styles.alternativa}>
          <Link href="/entrar">Sign in to Lettermusic</Link>
        </p>
      </>
    );
  }

  return (
    <form action={acao} className={styles.form}>
      <input type="hidden" name="token" value={token} />

      <label htmlFor="nova-senha">New password</label>
      <input
        id="nova-senha" name="senha_nova"
        type="password" autoComplete="new-password"
        minLength={12} maxLength={128} required
      />

      <label htmlFor="confirmar-nova-senha">
        Confirm new password
      </label>
      <input
        id="confirmar-nova-senha" name="confirmacao"
        type="password" autoComplete="new-password"
        minLength={12} maxLength={128} required
      />

      <Resultado {...estado} />
      <button type="submit" disabled={pendente}>
        {pendente ? "Resetting…" : "Save new password"}
      </button>
    </form>
  );
}

export function FormularioConfirmarEmail() {
  const parametros = useSearchParams();
  const token = parametros.get("token") ?? "";
  const [estado, acao, pendente] = useActionState(
    confirmarEmail, ESTADO_INICIAL
  );

  if (!TOKEN_VALIDO.test(token)) {
    return (
      <p role="alert" className={styles.mensagem}>
        Invalid link.{" "}
        <Link href="/reenviar-confirmacao">Request another link</Link>
      </p>
    );
  }

  if (estado.sucesso) {
    return (
      <>
        <Resultado {...estado} />
        <p className={styles.alternativa}>
          <Link href="/entrar">Go to sign in</Link>
        </p>
      </>
    );
  }

  return (
    <form action={acao} className={styles.form}>
      <input type="hidden" name="token" value={token} />
      <Resultado {...estado} />
      <button type="submit" disabled={pendente}>
        {pendente ? "Confirming…" : "Confirm email"}
      </button>
    </form>
  );
}
