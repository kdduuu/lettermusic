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
      <label htmlFor="email-recuperacao">E-mail cadastrado</label>
      <input
        id="email-recuperacao" name="email" type="email"
        autoComplete="email" maxLength={254} required
      />
      <Resultado {...estado} />
      <button type="submit" disabled={pendente}>
        {pendente ? "Enviando..." : "Enviar link de recuperação"}
      </button>
      <p className={styles.alternativa}>
        <Link href="/entrar">Voltar para o login</Link>
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
      <label htmlFor="email-confirmacao">E-mail cadastrado</label>
      <input
        id="email-confirmacao" name="email" type="email"
        defaultValue={emailInicial}
        autoComplete="email" maxLength={254} required
      />
      <Resultado {...estado} />
      <button type="submit" disabled={pendente}>
        {pendente ? "Enviando..." : "Reenviar confirmação"}
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
        Link inválido.{" "}
        <Link href="/esqueci-senha">Solicitar outro link</Link>
      </p>
    );
  }

  if (estado.sucesso) {
    return (
      <>
        <Resultado {...estado} />
        <p className={styles.alternativa}>
          <Link href="/entrar">Entrar no Lettermusic</Link>
        </p>
      </>
    );
  }

  return (
    <form action={acao} className={styles.form}>
      <input type="hidden" name="token" value={token} />

      <label htmlFor="nova-senha">Nova senha</label>
      <input
        id="nova-senha" name="senha_nova"
        type="password" autoComplete="new-password"
        minLength={12} maxLength={128} required
      />

      <label htmlFor="confirmar-nova-senha">
        Confirmar nova senha
      </label>
      <input
        id="confirmar-nova-senha" name="confirmacao"
        type="password" autoComplete="new-password"
        minLength={12} maxLength={128} required
      />

      <Resultado {...estado} />
      <button type="submit" disabled={pendente}>
        {pendente ? "Redefinindo..." : "Salvar nova senha"}
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
        Link inválido.{" "}
        <Link href="/reenviar-confirmacao">Solicitar outro link</Link>
      </p>
    );
  }

  if (estado.sucesso) {
    return (
      <>
        <Resultado {...estado} />
        <p className={styles.alternativa}>
          <Link href="/entrar">Ir para o login</Link>
        </p>
      </>
    );
  }

  return (
    <form action={acao} className={styles.form}>
      <input type="hidden" name="token" value={token} />
      <Resultado {...estado} />
      <button type="submit" disabled={pendente}>
        {pendente ? "Confirmando..." : "Confirmar e-mail"}
      </button>
    </form>
  );
}
