"use client";

import { useRef, useState } from "react";
import { CapaAlbum } from "@/components/capa-album";
import styles from "./faixas-interativas.module.css";

export type FaixaAlbum = {
  disco: number;
  numero: string;
  titulo: string;
  duracao_ms: number | null;
};

function duracao(ms: number | null) {
  if (ms === null) return null;
  const segundos = Math.floor(ms / 1000);
  return Math.floor(segundos / 60) + ":" + String(segundos % 60).padStart(2, "0");
}

export function FaixasInterativas({
  faixas, artista, capa,
}: {
  faixas: FaixaAlbum[];
  artista: string;
  capa: string | null;
}) {
  const dialogo = useRef<HTMLDialogElement>(null);
  const [selecionada, setSelecionada] = useState<FaixaAlbum | null>(null);

  function abrir(faixa: FaixaAlbum) {
    setSelecionada(faixa);
    if (dialogo.current && !dialogo.current.open) dialogo.current.showModal();
  }
  function fechar() {
    dialogo.current?.close();
  }

  return (
    <>
      <ol className={styles.faixas}>
        {faixas.map((faixa, indice) => (
          <li key={faixa.disco + "-" + faixa.numero + "-" + indice}>
            <button
              type="button"
              onClick={() => abrir(faixa)}
              aria-label={"Ver faixa " + faixa.titulo}
              className={styles.linha}
            >
              <span className={styles.numero}>{faixa.disco > 1 ? faixa.disco + "." : ""}{faixa.numero}</span>
              <span className={styles.titulo}>{faixa.titulo}</span>
              {duracao(faixa.duracao_ms) ? <time className={styles.duracao}>{duracao(faixa.duracao_ms)}</time> : null}
              <span className={styles.seta} aria-hidden="true">↗</span>
            </button>
          </li>
        ))}
      </ol>
      <dialog
        ref={dialogo}
        className={styles.dialogo}
        onClose={() => setSelecionada(null)}
        onClick={(event) => {
          if (event.target === event.currentTarget) fechar();
        }}
        aria-labelledby="titulo-faixa-modal"
      >
        <div className={styles.card}>
          <button type="button" className={styles.fechar} onClick={fechar} aria-label="Fechar">×</button>
          {selecionada ? (
            <>
              <CapaAlbum url={capa} titulo={selecionada.titulo} className={styles.capa} />
              <div className={styles.info}>
                <h3 id="titulo-faixa-modal">{selecionada.titulo}</h3>
                <p className={styles.artista}>{artista}</p>
                {duracao(selecionada.duracao_ms) ? (
                  <p className={styles.tempo}>{duracao(selecionada.duracao_ms)}</p>
                ) : null}
                <span className={styles.filete} aria-hidden="true" />
              </div>
            </>
          ) : <span id="titulo-faixa-modal" className={styles.oculto}>Faixa</span>}
        </div>
      </dialog>
    </>
  );
}
