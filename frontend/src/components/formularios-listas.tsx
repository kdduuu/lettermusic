"use client";

import { useActionState } from "react";
import {
  adicionarAlbumLista,
  criarLista,
  editarLista,
  excluirLista,
  moverAlbumLista,
  removerAlbumLista,
} from "@/app/acoes-listas";
import { ESTADO_INICIAL } from "@/lib/estado-acoes";
import type { ListaMusical } from "@/lib/listas";
import styles from "./formularios-listas.module.css";

function Mensagem({ sucesso, mensagem }: { sucesso: boolean; mensagem: string }) {
  if (!mensagem) return null;
  return <p role="status" className={sucesso ? styles.sucesso : styles.erro}>{mensagem}</p>;
}

export function FormularioCriarLista() {
  const [estado, acao, pendente] = useActionState(criarLista, ESTADO_INICIAL);
  return (
    <form action={acao} className={styles.form}>
      <label htmlFor="criar-titulo">List name</label>
      <input id="criar-titulo" name="titulo" maxLength={120} required placeholder="e.g. Indie nights" />
      <label htmlFor="criar-descricao">Description (optional)</label>
      <textarea id="criar-descricao" name="descricao" maxLength={500} rows={3} placeholder="What connects these albums?" />
      <label className={styles.checkbox}>
        <input type="checkbox" name="publica" defaultChecked /> Public list
      </label>
      <p className={styles.ajuda}>Private lists are only visible to you.</p>
      <button disabled={pendente} type="submit" className={styles.primario}>
        {pendente ? "Creating…" : "Create list"}
      </button>
      <Mensagem {...estado} />
    </form>
  );
}

export function FormularioEditarLista({ lista }: { lista: ListaMusical }) {
  const [estado, acao, pendente] = useActionState(editarLista, ESTADO_INICIAL);
  return (
    <form action={acao} className={styles.form}>
      <input type="hidden" name="lista_id" value={lista.id} />
      <label htmlFor="editar-titulo">List name</label>
      <input id="editar-titulo" name="titulo" defaultValue={lista.titulo} maxLength={120} required />
      <label htmlFor="editar-descricao">Description</label>
      <textarea id="editar-descricao" name="descricao" defaultValue={lista.descricao ?? ""} maxLength={500} rows={3} />
      <label className={styles.checkbox}>
        <input type="checkbox" name="publica" defaultChecked={lista.publica} /> Public list
      </label>
      <button disabled={pendente} type="submit">{pendente ? "Saving…" : "Save changes"}</button>
      <Mensagem {...estado} />
    </form>
  );
}

export function FormularioExcluirLista({ id }: { id: number }) {
  const [estado, acao, pendente] = useActionState(excluirLista, ESTADO_INICIAL);
  return (
    <details className={styles.excluir}>
      <summary>Delete list</summary>
      <p>The list and its items will be removed. Albums and listening history are kept.</p>
      <form action={acao}>
        <input type="hidden" name="lista_id" value={id} />
        <button type="submit" disabled={pendente} className={styles.perigo}>
          {pendente ? "Deleting…" : "Confirm deletion"}
        </button>
        <Mensagem {...estado} />
      </form>
    </details>
  );
}

export function FormularioAdicionarAlbum({
  idMusicBrainz,
  listas,
}: {
  idMusicBrainz: string;
  listas: ListaMusical[];
}) {
  const [estado, acao, pendente] = useActionState(adicionarAlbumLista, ESTADO_INICIAL);
  return (
    <form action={acao} className={styles.adicionar}>
      <input type="hidden" name="id_musicbrainz" value={idMusicBrainz} />
      <label htmlFor="album-lista">Add to a list</label>
      <div className={styles.linha}>
        <select name="lista_id" id="album-lista" required defaultValue="">
          <option value="" disabled>Choose a list</option>
          {listas.map((lista) => (
            <option key={lista.id} value={lista.id}>{lista.titulo}{lista.publica ? "" : " · Private"}</option>
          ))}
        </select>
        <button type="submit" disabled={pendente}>{pendente ? "Adding…" : "Add"}</button>
      </div>
      <Mensagem {...estado} />
    </form>
  );
}

export function BotaoAdicionarBusca({ id, listaId }: { id: string; listaId: number }) {
  const [estado, acao, pendente] = useActionState(adicionarAlbumLista, ESTADO_INICIAL);
  return (
    <form action={acao} className={styles.botaoBusca}>
      <input type="hidden" name="id_musicbrainz" value={id} />
      <input type="hidden" name="lista_id" value={listaId} />
      <button type="submit" disabled={pendente}>{pendente ? "Adding…" : "+ Add to list"}</button>
      <Mensagem {...estado} />
    </form>
  );
}

export function ControlesItemLista({
  listaId,
  obraId,
  posicao,
  podeDescer,
}: {
  listaId: number;
  obraId: number;
  posicao: number;
  podeDescer: boolean;
}) {
  const [acima, moverAcima, pendenteAcima] = useActionState(moverAlbumLista, ESTADO_INICIAL);
  const [abaixo, moverAbaixo, pendenteAbaixo] = useActionState(moverAlbumLista, ESTADO_INICIAL);
  const [remocao, remover, pendenteRemocao] = useActionState(removerAlbumLista, ESTADO_INICIAL);

  return (
    <div className={styles.controles}>
      <form action={moverAcima}>
        <input type="hidden" name="lista_id" value={listaId} />
        <input type="hidden" name="obra_id" value={obraId} />
        <input type="hidden" name="nova_posicao" value={Math.max(1, posicao - 1)} />
        <button type="submit" title="Move up" disabled={posicao <= 1 || pendenteAcima}>↑</button>
      </form>
      <form action={moverAbaixo}>
        <input type="hidden" name="lista_id" value={listaId} />
        <input type="hidden" name="obra_id" value={obraId} />
        <input type="hidden" name="nova_posicao" value={posicao + 1} />
        <button type="submit" title="Move down" disabled={!podeDescer || pendenteAbaixo}>↓</button>
      </form>
      <form action={remover}>
        <input type="hidden" name="lista_id" value={listaId} />
        <input type="hidden" name="obra_id" value={obraId} />
        <button type="submit" disabled={pendenteRemocao} title="Remove album from list">Remove</button>
      </form>
      {[acima, abaixo, remocao].filter((e) => e.mensagem).map((e, i) => <Mensagem key={i} {...e} />)}
    </div>
  );
}