
/** Ignora somente artigos iniciais; nunca altera o nome exibido ou a pesquisa. */
const ARTIGOS = new Set(["the", "a", "an", "o", "os", "as", "um", "uma", "el", "la", "los", "las", "le", "les"]);

export function monogramaArtista(nome: string): string {
  const palavras = nome.normalize("NFC").match(/[\p{L}\p{N}][\p{L}\p{M}\p{N}]*/gu) ?? [];
  const relevantes = palavras.length > 1 && ARTIGOS.has(palavras[0].toLowerCase())
    ? palavras.slice(1) : palavras;
  if (!relevantes.length) return "LM";
  const letras = relevantes.length > 1
    ? relevantes.slice(0, 2).map(palavra => Array.from(palavra)[0]).join("")
    : Array.from(relevantes[0]).slice(0, 2).join("");
  return letras.toLocaleUpperCase("pt-BR");
}

export function variacaoArtista(id: string): number {
  let hash = 0;
  for (const letra of id) hash = (Math.imul(hash, 31) + letra.charCodeAt(0)) | 0;
  return (hash >>> 0) % 3;
}
