"use client";

import { useActionState } from "react";
import { registrarInteracao } from "@/app/acoes";
import { ESTADO_INICIAL } from "@/lib/estado-acoes";
import styles from "./formulario-interacoes.module.css";

type TipoInteracao = "ouvida" | "favorito" | "quero-ouvir";

function AcaoAlbum({ id, tipo, rotulo }: {
  id: string;
  tipo: TipoInteracao;
  rotulo: string;
}) {
  const [estado, acao, pendente] = useActionState(registrarInteracao, ESTADO_INICIAL);

  return (
    <form action={acao} className={styles.acao}>
      <input type="hidden" name="id_musicbrainz" value={id} />
      <input type="hidden" name="tipo" value={tipo} />
      <button disabled={pendente} type="submit">{pendente ? "Salvando..." : rotulo}</button>
      {estado.mensagem && (
        <p className={estado.sucesso ? styles.sucesso : styles.erro} role="status">
          {estado.mensagem}
        </p>
      )}
    </form>
  );
}

export function FormularioInteracoes({ id }: { id: string }) {
  return (
    <div className={styles.grupo} aria-label="Registrar álbum na biblioteca">
      <AcaoAlbum id={id} tipo="ouvida" rotulo="Já ouvi" />
      <AcaoAlbum id={id} tipo="favorito" rotulo="Favoritar" />
      <AcaoAlbum id={id} tipo="quero-ouvir" rotulo="Quero ouvir" />
    </div>
  );
}