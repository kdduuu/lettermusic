import Link from "next/link";
import { Suspense } from "react";
import { sair } from "@/app/acoes";
import { obterUsuarioAutenticado } from "@/lib/sessao";
import styles from "./site-header.module.css";

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
        Buscar álbuns
      </label>
      <input
        id={id}
        name="termo"
        type="search"
        minLength={2}
        maxLength={100}
        required
        placeholder="Buscar álbuns..."
      />
      <button type="submit">Buscar</button>
    </form>
  );
}

async function AreaConta() {
  const usuario = await obterUsuarioAutenticado();

  if (!usuario) {
    return (
      <div className={styles.conta}>
        <Link href="/entrar">Entrar</Link>
        <Link href="/cadastro">Criar conta</Link>
      </div>
    );
  }

  return (
    <div className={styles.conta}>
      <Link href={`/usuarios/${encodeURIComponent(usuario.username)}`} title={`Ver perfil de ${usuario.nome_exibicao}`}>
        {usuario.username}
      </Link>
      <Link href="/biblioteca">Biblioteca</Link>
      <form action={sair}>
        <button type="submit">Sair</button>
      </form>
    </div>
  );
}

export function SiteHeader() {
  return (
    <header className={styles.header}>
      <div className={styles.inner}>
        <Link className={styles.brand} href="/" aria-label="Lettermusic, início">
          Lettermusic<span aria-hidden="true">*</span>
        </Link>
        <nav className={styles.nav} aria-label="Navegação principal">
          <Link href="/">Descobrir</Link>
          <span title="Em desenvolvimento">Álbuns</span>
          <span title="Em desenvolvimento">Reviews</span>
          <Link href="/listas">Listas</Link>
          <span title="Em desenvolvimento">Comunidade</span>
        </nav>
        <SearchForm />
        <Suspense fallback={<span className={styles.aguardando}>Conta</span>}>
          <AreaConta />
        </Suspense>
      </div>
    </header>
  );
}