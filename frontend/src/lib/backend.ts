// Cliente HTTP do servidor Next.js para a API FastAPI.
// Não importar em componentes com "use client".
export function enderecoBackend(): string {
  return (process.env.BACKEND_URL ?? "http://127.0.0.1:8000").replace(/\/$/, "");
}

export async function requisitarBackend(
  caminho: string,
  opcoes: RequestInit = {},
): Promise<Response> {
  // O caminho é definido em módulos confiáveis do servidor, nunca pela URL do usuário.
  const cabecalhos = new Headers(opcoes.headers);
  if (opcoes.body && !cabecalhos.has("Content-Type")) {
    cabecalhos.set("Content-Type", "application/json");
  }

  return fetch(`${enderecoBackend()}${caminho}`, {
    ...opcoes,
    headers: cabecalhos,
    cache: "no-store",
    signal: AbortSignal.timeout(20_000),
  });
}