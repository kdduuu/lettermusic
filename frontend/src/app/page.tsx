import { SearchForm } from "@/components/site-header";
import styles from "./page.module.css";

export default function Home() {
  return (
    <main className={styles.container}>
      <section className={styles.hero}>
        <span className={styles.accent} aria-hidden="true" />
        <h1>Descobrir</h1>
        <p>Encontre álbuns para registrar, avaliar e compartilhar.</p>
        <SearchForm variant="hero" />
      </section>
    </main>
  );
}