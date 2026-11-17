"use client";

import { useActionState } from "react";
import { salvarAvaliacao, salvarReview } from "@/app/acoes";
import { ESTADO_INICIAL } from "@/lib/estado-acoes";
import type { EstadoAlbum } from "@/lib/estado-album";
import styles from "./formulario-avaliacao.module.css";

const NOTAS = Array.from({ length: 10 }, (_, indice) => (indice + 1) / 2);

export function FormularioAvaliacao({ id, estado }: { id: string; estado: EstadoAlbum }) {
  const [resultadoNota, avaliar, salvandoNota] = useActionState(salvarAvaliacao, ESTADO_INICIAL);
  const [resultadoReview, publicar, salvandoReview] = useActionState(salvarReview, ESTADO_INICIAL);

  return (
    <section className={styles.container} aria-label="Avaliar e escrever review">
      <form action={avaliar} className={styles.avaliacao}>
        <input type="hidden" name="id_musicbrainz" value={id} />
        <label htmlFor={`nota-${id}`}>Sua avaliação</label>
        <div className={styles.linha}>
          <select id={`nota-${id}`} name="nota" defaultValue={estado.nota?.toString() ?? ""} required>
            <option value="" disabled>Selecione uma nota</option>
            {NOTAS.map((nota) => (
              <option key={nota} value={nota}>{nota.toLocaleString("pt-BR")} ★</option>
            ))}
          </select>
          <button disabled={salvandoNota} type="submit">
            {salvandoNota ? "Salvando..." : estado.nota !== null ? "Atualizar nota" : "Avaliar"}
          </button>
        </div>
        {resultadoNota.mensagem && (
          <p className={resultadoNota.sucesso ? styles.sucesso : styles.erro} role="status">
            {resultadoNota.mensagem}
          </p>
        )}
      </form>

      <form action={publicar} className={styles.review}>
        <input type="hidden" name="id_musicbrainz" value={id} />
        <label htmlFor={`review-${id}`}>Sua review</label>
        <textarea
          id={`review-${id}`} name="texto" maxLength={5000} minLength={1}
          required rows={4} defaultValue={estado.review ?? ""}
          placeholder="O que você achou deste álbum?"
        />
        <button disabled={salvandoReview} type="submit">
          {salvandoReview ? "Salvando..." : estado.review !== null ? "Atualizar review" : "Publicar review"}
        </button>
        {resultadoReview.mensagem && (
          <p className={resultadoReview.sucesso ? styles.sucesso : styles.erro} role="status">
            {resultadoReview.mensagem}
          </p>
        )}
      </form>
      <p className={styles.nota}>A primeira avaliação ou review registra automaticamente uma escuta; editar não.</p>
    </section>
  );
}