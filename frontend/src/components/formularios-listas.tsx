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
      <label htmlFor="criar-titulo">Nome da lista</label>
      <input id="criar-titulo" name="titulo" maxLength={120} required placeholder="Ex.: Noite Indie" />
      <label htmlFor="criar-descricao">Descrição (opcional)</label>
      <textarea id="criar-descricao" name="descricao" maxLength={500} rows={3} placeholder="O que reúne esses álbuns?" />
      <label className={styles.checkbox}>
        <input type="checkbox" name="publica" defaultChecked /> Lista pública
      </label>
      <p className={styles.ajuda}>Listas privadas ficam visíveis apenas para sua conta.</p>
      <button disabled={pendente} type="submit" className={styles.primario}>
        {pendente ? "Criando..." : "Criar lista"}
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
      <label htmlFor="editar-titulo">Nome da lista</label>
      <input id="editar-titulo" name="titulo" defaultValue={lista.titulo} maxLength={120} required />
      <label htmlFor="editar-descricao">Descrição</label>
      <textarea id="editar-descricao" name="descricao" defaultValue={lista.descricao ?? ""} maxLength={500} rows={3} />
      <label className={styles.checkbox}>
        <input type="checkbox" name="publica" defaultChecked={lista.publica} /> Lista pública
      </label>
      <button disabled={pendente} type="submit">{pendente ? "Salvando..." : "Salvar alterações"}</button>
      <Mensagem {...estado} />
    </form>
  );
}

export function FormularioExcluirLista({ id }: { id: number }) {
  const [estado, acao, pendente] = useActionState(excluirLista, ESTADO_INICIAL);
  return (
    <details className={styles.excluir}>
      <summary>Excluir esta lista</summary>
      <p>A lista e seus itens serão removidos. As obras e escutas do catálogo permanecem.</p>
      <form action={acao}>
        <input type="hidden" name="lista_id" value={id} />
        <button type="submit" disabled={pendente} className={styles.perigo}>
          {pendente ? "Excluindo..." : "Confirmar exclusão"}
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
      <label htmlFor="album-lista">Adicionar a uma lista</label>
      <div className={styles.linha}>
        <select name="lista_id" id="album-lista" required defaultValue="">
          <option value="" disabled>Escolha uma lista</option>
          {listas.map((lista) => (
            <option key={lista.id} value={lista.id}>{lista.titulo}{lista.publica ? "" : " · Privada"}</option>
          ))}
        </select>
        <button type="submit" disabled={pendente}>{pendente ? "Adicionando..." : "Adicionar"}</button>
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
      <button type="submit" disabled={pendente}>{pendente ? "Adicionando..." : "+ Adicionar à lista"}</button>
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
        <button type="submit" title="Subir uma posição" disabled={posicao <= 1 || pendenteAcima}>↑</button>
      </form>
      <form action={moverAbaixo}>
        <input type="hidden" name="lista_id" value={listaId} />
        <input type="hidden" name="obra_id" value={obraId} />
        <input type="hidden" name="nova_posicao" value={posicao + 1} />
        <button type="submit" title="Descer uma posição" disabled={!podeDescer || pendenteAbaixo}>↓</button>
      </form>
      <form action={remover}>
        <input type="hidden" name="lista_id" value={listaId} />
        <input type="hidden" name="obra_id" value={obraId} />
        <button type="submit" disabled={pendenteRemocao} title="Remover álbum da lista">Remover</button>
      </form>
      {[acima, abaixo, remocao].filter((e) => e.mensagem).map((e, i) => <Mensagem key={i} {...e} />)}
    </div>
  );
}