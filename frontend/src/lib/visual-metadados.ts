const TIPOS: Record<string, string> = {
  album: "Album", single: "Single", ep: "EP", compilation: "Compilation",
  live: "Live", group: "Group", person: "Person", orchestra: "Orchestra",
  choir: "Choir", character: "Character", other: "Other",
};

export function tipoMusicalEmPortugues(tipo: string | null | undefined) {
  return tipo ? TIPOS[tipo.toLowerCase()] ?? tipo : tipo;
}
