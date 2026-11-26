"use client";

import Link from "next/link";
import { useActionState, useState } from "react";
import { buscarFavoritosPerfil, salvarFavoritosPerfil } from "@/app/acoes-favoritos-perfil";
import { ESTADO_INICIAL } from "@/lib/estado-acoes";
import type { AlbumFavorito } from "@/lib/perfis";
import { CapaAlbum } from "@/components/capa-album";
import { UiIcon } from "@/components/ui-icon";
import styles from "./favoritos-perfil.module.css";

function Cover({album}: {album: AlbumFavorito}) {
  return <CapaAlbum key={album.id_musicbrainz} url={"https://coverartarchive.org/release-group/" + album.id_musicbrainz.toLowerCase() + "/front-500"} titulo={album.titulo} className={styles.cover}/>;
}

function Editor({albuns, fechar}: {albuns: AlbumFavorito[]; fechar: () => void}) {
  const [selected, setSelected] = useState(albuns);
  const [search, buscar, searching] = useActionState(buscarFavoritosPerfil, {albuns: [], mensagem: ""});
  const [saved, salvar, saving] = useActionState(salvarFavoritosPerfil, ESTADO_INICIAL);
  function move(index: number, delta: number) {
    setSelected(items => {
      const next = [...items];
      const dest = index + delta;
      if (dest < 0 || dest >= next.length) return items;
      [next[index], next[dest]] = [next[dest], next[index]];
      return next;
    });
  }
  return <div className={styles.editor}>
    <div className={styles.editorHead}><strong>Edit profile favorites · {selected.length}/4</strong><button type="button" onClick={fechar} className={styles.icon} aria-label="Close editor" title="Close editor">×</button></div>
    <ol className={styles.selected}>
      {selected.map((album,i) => <li key={album.id_musicbrainz}>
        <Cover album={album}/>
        <span className={styles.albumInfo}><strong>{album.titulo}</strong><small>{album.artista ?? "Unknown artist"}</small></span>
        <div className={styles.controls}>
          <button type="button" className={styles.icon} disabled={i===0 || saving} onClick={()=>move(i,-1)} aria-label={"Move "+album.titulo+" earlier"} title="Move earlier"><UiIcon name="arrow-up" size={16}/></button>
          <button type="button" className={styles.icon} disabled={i===selected.length-1 || saving} onClick={()=>move(i,1)} aria-label={"Move "+album.titulo+" later"} title="Move later"><UiIcon name="arrow-down" size={16}/></button>
          <button type="button" className={styles.icon} disabled={saving} onClick={()=>setSelected(items=>items.filter(item=>item.id_musicbrainz!==album.id_musicbrainz))} aria-label={"Remove "+album.titulo} title="Remove"><UiIcon name="trash" size={16}/></button>
        </div>
      </li>)}
    </ol>
    <form action={buscar} className={styles.search}>
      <input name="termo" minLength={2} maxLength={100} required placeholder="Album or artist…" aria-label="Search albums"/>
      <button className={styles.icon} type="submit" disabled={searching || saving} aria-label="Search" title="Search"><UiIcon name="search" size={18}/></button>
    </form>
    {searching ? <p role="status">Searching…</p> : null}
    {search.mensagem && !searching ? <p role="status">{search.mensagem}</p> : null}
    <ul className={styles.results}>
      {search.albuns.map(album => {
        const chosen = selected.some(item=>item.id_musicbrainz===album.id_musicbrainz);
        return <li key={album.id_musicbrainz}><Cover album={album}/><span className={styles.albumInfo}><strong>{album.titulo}</strong><small>{album.artista ?? "Unknown artist"}</small></span>
          <button className={styles.icon} type="button" disabled={chosen || selected.length>=4 || saving} aria-label={chosen?"Already selected": "Add "+album.titulo} title={chosen?"Already selected":"Add album"} onClick={()=>setSelected(items=>items.length<4&&!items.some(a=>a.id_musicbrainz===album.id_musicbrainz)?[...items,album]:items)}><UiIcon name={chosen?"check-circle":"plus"} size={18}/></button>
        </li>;
      })}
    </ul>
    <form action={salvar} className={styles.save}>
      {selected.map(album=><input key={album.id_musicbrainz} type="hidden" name="album" value={album.id_musicbrainz}/>)}
      <button type="submit" disabled={saving}>{saving?"Saving…":"Save"}</button>
      {saved.mensagem?<p role="status">{saved.mensagem}</p>:null}
    </form>
  </div>;
}

export function FavoritosPerfil({albuns,dono}: {albuns: AlbumFavorito[]; dono: boolean}) {
  const [editing,setEditing] = useState(false);
  return <section className={styles.section} aria-label="Favorite albums">
    <div className={styles.line}>
      <div className={styles.grid}>
        {albuns.map(album=><Link href={"/albuns/"+encodeURIComponent(album.id_musicbrainz)} key={album.id_musicbrainz} title={album.titulo+" — "+(album.artista??"Unknown artist")} aria-label={album.titulo+" — "+(album.artista??"Unknown artist")} className={styles.album}><Cover album={album}/></Link>)}
        {dono && Array.from({length:4-albuns.length},(_,i)=><button key={"empty-"+i} type="button" className={styles.empty} onClick={()=>setEditing(true)} aria-label="Choose favorite album" title="Choose favorite album"><UiIcon name="plus" size={23}/></button>)}
      </div>
      {dono?<button type="button" className={styles.icon} onClick={()=>setEditing(!editing)} aria-expanded={editing} title="Edit profile favorites" aria-label="Edit profile favorites"><UiIcon name="pen" size={18}/></button>:null}
    </div>
    {editing&&dono?<Editor albuns={albuns} fechar={()=>setEditing(false)}/>:null}
  </section>;
}
