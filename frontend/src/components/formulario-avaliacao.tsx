"use client";

import { useActionState } from "react";
import { salvarAvaliacao, salvarReview, removerReview } from "@/app/acoes";
import { ESTADO_INICIAL } from "@/lib/estado-acoes";
import type { EstadoAlbum } from "@/lib/estado-album";
import styles from "./formulario-avaliacao.module.css";

const NOTAS = Array.from({ length: 10 }, (_, indice) => (indice + 1) / 2);

export function FormularioAvaliacao({ id, estado }: { id: string; estado: EstadoAlbum }) {
  const [resultadoNota, avaliar, salvandoNota] = useActionState(salvarAvaliacao, ESTADO_INICIAL);
  const [resultadoReview, publicar, salvandoReview] = useActionState(salvarReview, ESTADO_INICIAL);
  const [resultadoRemocao, excluir, excluindo] = useActionState(removerReview, ESTADO_INICIAL);

  return (
    <section className={styles.container} aria-label="Rate and review">
      <form action={avaliar} className={styles.avaliacao}>
        <input type="hidden" name="id_musicbrainz" value={id} />
        <label htmlFor={`nota-${id}`}>Your rating</label>
        <div className={styles.linha}>
          <select id={`nota-${id}`} name="nota" defaultValue={estado.nota?.toString() ?? ""} required>
            <option value="" disabled>Choose a rating</option>
            {NOTAS.map((nota) => (
              <option key={nota} value={nota}>{nota.toLocaleString("pt-BR")} ★</option>
            ))}
          </select>
          <button disabled={salvandoNota} type="submit">
            {salvandoNota ? "Saving…" : estado.nota !== null ? "Update rating" : "Rate"}
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
        <label htmlFor={`review-${id}`}>Your review</label>
        <textarea
          id={`review-${id}`} name="texto" maxLength={5000} minLength={1}
          required rows={4} defaultValue={estado.review ?? ""}
          placeholder="What did you think of this album?"
        />
        <button disabled={salvandoReview} type="submit">
          {salvandoReview ? "Saving…" : estado.review !== null ? "Update review" : "Publish review"}
        </button>
        {resultadoReview.mensagem && (
          <p className={resultadoReview.sucesso ? styles.sucesso : styles.erro} role="status">
            {resultadoReview.mensagem}
          </p>
        )}
      </form>

      {estado.review !== null ? (
        <form
          action={excluir}
          className={styles.review}
          onSubmit={(evento) => {
            if (!window.confirm("Delete your review of this album?")) {
              evento.preventDefault();
            }
          }}
        >
          <input
            type="hidden"
            name="id_musicbrainz"
            value={id}
          />
          <button
            type="submit"
            className={styles.botaoExcluir}
            disabled={excluindo}
          >
            {excluindo ? "Deleting…" : "Delete review"}
          </button>
          {resultadoRemocao.mensagem && (
            <p
              role="status"
              className={resultadoRemocao.sucesso ? styles.sucesso : styles.erro}
            >
              {resultadoRemocao.mensagem}
            </p>
          )}
        </form>
      ) : null}

      <p className={styles.nota}>Your first rating or review logs a play. Editing does not.</p>
    </section>
  );
}