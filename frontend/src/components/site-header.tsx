import { UiIcon } from "@/components/ui-icon";
import Link from "next/link";
import { Suspense } from "react";
import { sair } from "@/app/acoes";
import { obterUsuarioAutenticado } from "@/lib/sessao";
import styles from "./site-header.module.css";
import { NavegacaoPrincipal, NavegacaoPrincipalEstatica } from "./navegacao-principal";

type SearchFormProps = {
  variant?: "header" | "hero";
};

export function SearchForm({ variant = "header" }: SearchFormProps) {
  const id = variant === "hero" ? "busca-principal" : "busca-cabecalho";

  return (
    <form
      action="/buscar"
      method="get"
      role="search"
      className={`${styles.search} ${variant === "hero" ? styles.heroSearch : ""}`}
    >
      <label htmlFor={id} className={styles.srOnly}>
        Search music
      </label>
      <input
        id={id}
        name="termo"
        type="search"
        minLength={2}
        maxLength={100}
        required
        placeholder="Album, artist or track…"
      />
      <button type="submit" title="Search" aria-label="Search"><UiIcon name="search" size={17}/></button>
    </form>
  );
}

async function AreaConta() {
  const usuario = await obterUsuarioAutenticado();

  if (!usuario) {
    return (
      <div className={styles.conta}>
        <Link href="/entrar">Sign in</Link>
        <Link href="/cadastro">Sign up</Link>
      </div>
    );
  }

  return (
    <div className={styles.conta}>
      <Link href={`/usuarios/${encodeURIComponent(usuario.username)}`} title={`View profile of ${usuario.nome_exibicao}`}>
        {usuario.username}
      </Link>
      <Link href="/biblioteca">Library</Link>
      <Link href="/conta">Account</Link>
      <form action={sair}>
        <button type="submit">Sign out</button>
      </form>
    </div>
  );
}

export function SiteHeader() {
  return (
    <header className={styles.header}>
      <div className={styles.inner}>
        <Link className={styles.brand} href="/" aria-label="Lettermusic, home">
          Lettermusic<span aria-hidden="true">*</span>
        </Link>
        <Suspense fallback={<NavegacaoPrincipalEstatica />}>
          <NavegacaoPrincipal />
        </Suspense>
        <SearchForm />
        <Suspense fallback={<span className={styles.aguardando}>Account</span>}>
          <AreaConta />
        </Suspense>
      </div>
    </header>
  );
}