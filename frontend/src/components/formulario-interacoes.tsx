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
    return <span className={styles.confirmado}>✓ Já ouvi</span>;
  }

  return (
    <form action={acao} className={styles.acao}>
      <input type="hidden" name="id_musicbrainz" value={id} />
      <input type="hidden" name="tipo" value={tipo} />
      <input type="hidden" name="operacao" value={ativo ? "remover" : "adicionar"} />
      <button disabled={pendente} type="submit">
        {pendente ? "Salvando..." : ativo ? `✓ ${rotulo} · Remover` : rotulo}
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
        {pendente ? "Registrando..." : "Registrar escuta"}
      </button>
      <span className={styles.contador}>
        {quantidade} {quantidade === 1 ? "escuta registrada" : "escutas registradas"}
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
    <section className={styles.container} aria-label="Seus registros deste álbum">
      <h2>Seus registros</h2>
      <div className={styles.grupo}>
        <AcaoAlbum id={id} tipo="ouvida" ativo={estado.ouvida} rotulo="Já ouvi" />
        <AcaoAlbum id={id} tipo="favorito" ativo={estado.favorito} rotulo="Favorito" />
        <AcaoAlbum id={id} tipo="quero-ouvir" ativo={estado.quero_ouvir} rotulo="Quero ouvir" />
      </div>
      <AcaoEscuta id={id} quantidade={estado.quantidade_escutas} />
    </section>
  );
}