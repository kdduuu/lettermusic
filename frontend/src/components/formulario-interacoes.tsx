"use client";
import { useActionState } from "react";
import { registrarEscuta, registrarInteracao } from "@/app/acoes";
import { ESTADO_INICIAL } from "@/lib/estado-acoes";
import type { EstadoAlbum } from "@/lib/estado-album";
import { UiIcon, type IconName } from "@/components/ui-icon";
import styles from "./social-actions.module.css";
type Tipo = "ouvida" | "favorito" | "quero-ouvir";
function Acao({ id, tipo, ativo, label, icon }: { id:string; tipo:Tipo; ativo:boolean; label:string; icon:IconName }) {
  const [r, action, pending] = useActionState(registrarInteracao, ESTADO_INICIAL);
  const done = tipo === "ouvida" && ativo;
  return <form action={action} className={styles.action}>
    <input type="hidden" name="id_musicbrainz" value={id}/><input type="hidden" name="tipo" value={tipo}/><input type="hidden" name="operacao" value={ativo ? "remover":"adicionar"}/>
    <button type="submit" disabled={pending || done} aria-pressed={ativo} aria-label={label} title={done ? "Already listened" : ativo ? "Remove: "+label : label} className={styles.iconAction}><UiIcon name={icon}/><span>{label}</span></button>
    {r.mensagem ? <p role="status" className={r.sucesso ? styles.success : styles.error}>{r.mensagem}</p>:null}
  </form>;
}
export function FormularioInteracoes({id,estado}:{id:string;estado:EstadoAlbum}) {
  const [r,action,pending]=useActionState(registrarEscuta,ESTADO_INICIAL);
  return <section aria-label="Your album activity" className={styles.interactions}>
    <div className={styles.actionGrid}>
      <Acao id={id} tipo="ouvida" ativo={estado.ouvida} label="Listened" icon="check-circle"/>
      <Acao id={id} tipo="favorito" ativo={estado.favorito} label="Favorite" icon="heart"/>
      <Acao id={id} tipo="quero-ouvir" ativo={estado.quero_ouvir} label="Later" icon="bookmark"/>
    </div>
    <form action={action} className={styles.play}>
      <input type="hidden" name="id_musicbrainz" value={id}/>
      <button type="submit" disabled={pending} className={styles.actionLink} aria-label="Log a play" title="Log a play"><UiIcon name="headphones"/> <span>Log a play</span></button>
      <span className={styles.count}>{estado.quantidade_escutas} {estado.quantidade_escutas===1?"play":"plays"}</span>
      {r.mensagem ? <p role="status" className={r.sucesso ? styles.success : styles.error}>{r.mensagem}</p>:null}
    </form>
  </section>;
}