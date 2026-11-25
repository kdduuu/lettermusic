"use client";

import { useActionState } from "react";
import { registrarEscuta, registrarInteracao } from "@/app/acoes";
import { ESTADO_INICIAL } from "@/lib/estado-acoes";
import type { EstadoAlbum } from "@/lib/estado-album";
import styles from "./formulario-interacoes.module.css";

type TipoInteracao = "ouvida" | "favorito" | "quero-ouvir";

function AcaoAlbum({ id, tipo, ativo, rotulo }: {
  id: string;
  tipo: TipoInteracao;
  ativo: boolean;
  rotulo: string;
}) {
  const [estado, acao, pendente] = useActionState(registrarInteracao, ESTADO_INICIAL);

  if (tipo === "ouvida" && ativo) {
    return <span className={styles.confirmado}>✓ Listened</span>;
  }

  return (
    <form action={acao} className={styles.acao}>
      <input type="hidden" name="id_musicbrainz" value={id} />
      <input type="hidden" name="tipo" value={tipo} />
      <input type="hidden" name="operacao" value={ativo ? "remover" : "adicionar"} />
      <button disabled={pendente} type="submit" aria-pressed={tipo === "ouvida" ? undefined : ativo} title={ativo ? `Remove: ${rotulo}` : undefined}>
        {pendente ? "Saving…" : ativo ? `✓ ${rotulo}` : rotulo}
      </button>
      {estado.mensagem && (
        <p className={estado.sucesso ? styles.sucesso : styles.erro} role="status">
          {estado.mensagem}
        </p>
      )}
    </form>
  );
}

function AcaoEscuta({ id, quantidade }: { id: string; quantidade: number }) {
  const [estado, acao, pendente] = useActionState(registrarEscuta, ESTADO_INICIAL);

  return (
    <form action={acao} className={styles.escuta}>
      <input type="hidden" name="id_musicbrainz" value={id} />
      <button type="submit" disabled={pendente}>
        {pendente ? "Logging…" : "Log a play"}
      </button>
      <span className={styles.contador}>
        {quantidade} {quantidade === 1 ? "play logged" : "plays logged"}
      </span>
      {estado.mensagem && (
        <p className={estado.sucesso ? styles.sucesso : styles.erro} role="status">
          {estado.mensagem}
        </p>
      )}
    </form>
  );
}

export function FormularioInteracoes({ id, estado }: { id: string; estado: EstadoAlbum }) {
  return (
    <section className={styles.container} aria-label="Your album activity">
      <h2>Your activity</h2>
      <div className={styles.grupo}>
        <AcaoAlbum id={id} tipo="ouvida" ativo={estado.ouvida} rotulo="Listened" />
        <AcaoAlbum id={id} tipo="favorito" ativo={estado.favorito} rotulo="Favorite" />
        <AcaoAlbum id={id} tipo="quero-ouvir" ativo={estado.quero_ouvir} rotulo="Want to listen" />
      </div>
      <AcaoEscuta id={id} quantidade={estado.quantidade_escutas} />
    </section>
  );
}