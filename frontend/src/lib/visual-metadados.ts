const TIPOS: Record<string, string> = {
  album: "Álbum", single: "Single", ep: "EP", compilation: "Coletânea",
  live: "Ao vivo", group: "Grupo", person: "Pessoa", orchestra: "Orquestra",
  choir: "Coral", character: "Personagem", other: "Outro",
};

export function tipoMusicalEmPortugues(tipo: string | null | undefined) {
  return tipo ? TIPOS[tipo.toLowerCase()] ?? tipo : tipo;
}
