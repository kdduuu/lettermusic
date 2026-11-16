// Contrato serializável de resposta das Server Actions para componentes React.
export type EstadoAcao = { sucesso: boolean; mensagem: string };
export const ESTADO_INICIAL: EstadoAcao = { sucesso: false, mensagem: "" };