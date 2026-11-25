"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import styles from "./site-header.module.css";

const rotas = [
  { href: "/", prefixo: "/", titulo: "Discover" },
  { href: "/albuns", prefixo: "/albuns", titulo: "Albums" },
  { href: "/reviews", prefixo: "/reviews", titulo: "Reviews" },
  { href: "/listas/explorar", prefixo: "/listas", titulo: "Lists" },
  { href: "/comunidade", prefixo: "/comunidade", titulo: "Community" },
] as const;

function LinksPrincipais({ pathname }: { pathname: string }) {
  return (
    <nav className={styles.nav} aria-label="Main navigation">
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
