"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import styles from "./site-header.module.css";

const rotas = [
  { href: "/", prefixo: "/", titulo: "Descobrir" },
  { href: "/albuns", prefixo: "/albuns", titulo: "Álbuns" },
  { href: "/reviews", prefixo: "/reviews", titulo: "Reviews" },
  { href: "/listas/explorar", prefixo: "/listas", titulo: "Listas" },
  { href: "/comunidade", prefixo: "/comunidade", titulo: "Comunidade" },
] as const;

function LinksPrincipais({ pathname }: { pathname: string }) {
  return (
    <nav className={styles.nav} aria-label="Navegação principal">
      {rotas.map(({ href, prefixo, titulo }) => {
        const ativa = pathname === href || (prefixo !== "/" &&
          (pathname === prefixo || pathname.startsWith(prefixo + "/")));
        return <Link key={href} href={href} aria-current={ativa ? pathname === href ? "page" : "location" : undefined}>{titulo}</Link>;
      })}
    </nav>
  );
}

export function NavegacaoPrincipal() {
  const pathname = usePathname();
  return <LinksPrincipais pathname={pathname ?? ""} />;
}

export function NavegacaoPrincipalEstatica() {
  return <LinksPrincipais pathname="" />;
}
