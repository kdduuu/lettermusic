/** Inicial visual: ignora artigos iniciais sem alterar o nome original. */
const ARTIGOS = new Set(["the", "a", "an", "o", "os", "as", "um", "uma", "el", "la", "los", "las", "le", "les"]);

export function monogramaArtista(nome: string): string {
  const palavras = nome.normalize("NFC").match(/[\p{L}\p{N}][\p{L}\p{M}\p{N}]*/gu) ?? [];
  const relevante = palavras.length > 1 && ARTIGOS.has(palavras[0].toLowerCase())
    ? palavras[1] : palavras[0];
  if (!relevante) return "♪";
  return Array.from(Array.from(relevante)[0].toLocaleUpperCase("pt-BR"))[0];
}
