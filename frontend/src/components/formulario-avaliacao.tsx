"use client";
import { useActionState } from "react";
import { salvarAvaliacao, salvarReview, removerReview } from "@/app/acoes";
import { ESTADO_INICIAL } from "@/lib/estado-acoes";
import type { EstadoAlbum } from "@/lib/estado-album";
import { UiIcon } from "@/components/ui-icon";
import styles from "./social-actions.module.css";
export function FormularioAvaliacao({id,estado}:{id:string;estado:EstadoAlbum}) {
  const [rating,rate,saving]=useActionState(salvarAvaliacao,ESTADO_INICIAL);
  const [review,publish,publishing]=useActionState(salvarReview,ESTADO_INICIAL);
  const [removed,remove,removing]=useActionState(removerReview,ESTADO_INICIAL);
  return <section className={styles.ratingArea} aria-label="Rate and review">
    <form action={rate}>
      <input type="hidden" name="id_musicbrainz" value={id}/>
      <div className={styles.ratingHeading}><span>Your rating</span><strong>{estado.nota === null ? "—" : estado.nota.toFixed(1)}</strong></div>
      <div className={styles.stars} role="group" aria-label="Rate in half-star increments">
        {Array.from({length:5},(_,i)=><span className={styles.starPair} key={i}>
          {[0.5,1].map((part)=><button key={part} type="submit" name="nota" value={i+part} disabled={saving} aria-label={`Rate ${i+part} out of 5 stars`} title={`${i+part} stars`} data-filled={(estado.nota??0)>=i+part} className={part===0.5?styles.halfLeft:styles.halfRight}><span aria-hidden="true">★</span></button>)}
        </span>)}
      </div>
      {rating.mensagem ? <p role="status" className={rating.sucesso?styles.success:styles.error}>{rating.mensagem}</p>:null}
    </form>
    <details className={styles.disclosure}>
      <summary title={estado.review===null?"Write a review":"Edit review"}><UiIcon name="pen"/><span>{estado.review===null?"Write a review":"Edit review"}</span><UiIcon name="chevron-right"/></summary>
      <form action={publish} className={styles.editor}>
        <input type="hidden" name="id_musicbrainz" value={id}/>
        <textarea aria-label="Your review" name="texto" maxLength={5000} required rows={4} defaultValue={estado.review??""} placeholder="Your thoughts…"/>
        <button type="submit" disabled={publishing}>{publishing?"Saving…":estado.review===null?"Publish":"Save"}</button>
        {review.mensagem?<p role="status" className={review.sucesso?styles.success:styles.error}>{review.mensagem}</p>:null}
      </form>
      {estado.review!==null?<form action={remove} onSubmit={e=>{if(!window.confirm("Delete your review?"))e.preventDefault();}}>
        <input type="hidden" name="id_musicbrainz" value={id}/>
        <button className={styles.delete} type="submit" disabled={removing} aria-label="Delete review" title="Delete review"><UiIcon name="trash"/></button>
        {removed.mensagem?<p role="status" className={removed.sucesso?styles.success:styles.error}>{removed.mensagem}</p>:null}
      </form>:null}
    </details>
    <p className={styles.hint}>First rating or review logs a play.</p>
  </section>;
}