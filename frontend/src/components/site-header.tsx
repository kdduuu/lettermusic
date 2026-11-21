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
        Buscar músicas
      </label>
      <input
        id={id}
        name="termo"
        type="search"
        minLength={2}
        maxLength={100}
        required
        placeholder="Álbum, artista ou faixa..."
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
      <Link href="/conta">Conta</Link>
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
          <Link href="/albuns">Álbuns</Link>
          <Link href="/reviews">Reviews</Link>
          <Link href="/listas/explorar">Listas</Link>
          <Link href="/comunidade">Comunidade</Link>
        </nav>
        <SearchForm />
        <Suspense fallback={<span className={styles.aguardando}>Conta</span>}>
          <AreaConta />
        </Suspense>
      </div>
    </header>
  );
}