/** Inicial visual: ignora artigos iniciais sem alterar o nome original. */
const ARTIGOS = new Set(["the", "a", "an", "o", "os", "as", "um", "uma", "el", "la", "los", "las", "le", "les"]);

export function monogramaArtista(nome: string): string {
  const palavras = nome.normalize("NFC").match(/[\p{L}\p{N}][\p{L}\p{M}\p{N}]*/gu) ?? [];
  const [primeira, segunda] = palavras;
  if (!primeira) return "♪";
  const relevante = segunda && ARTIGOS.has(primeira.toLowerCase()) ? segunda : primeira;
  const inicial = Array.from(relevante)[0]?.toLocaleUpperCase("pt-BR") ?? "♪";
  return Array.from(inicial)[0] ?? "♪";
}
