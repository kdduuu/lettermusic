# F11 — Seguranca e confiabilidade

## F11.1 — Base do rate limiting persistente

- Uma branch para toda a F11; main preservada.
- PostgreSQL compartilhado, sem nova infraestrutura. SQLite somente para testes.
- Contadores por chave HMAC, janela fixa a partir da primeira reserva, UPSERT
  condicional e transacao independente. Todas as regras sao aceitas ou revertidas.
- Migration f11a1c9e014f; limpeza de registros expirados disponivel.
- Testes de persistencia, expiracao, rollback, limpeza e concorrencia PostgreSQL.

Esta base ainda nao substitui os limitadores HTTP existentes. Proxima etapa:
integrar login, cadastro e recuperacao, definir segredo e origem confiavel
Next.js/FastAPI, tratar indisponibilidade e programar limpeza antes do deploy.
Janelas fixas admitem rajadas na transicao; nao equivalem a janelas deslizantes.
Nenhum deploy. Validar migration e CI antes de integrar.

## F11.2 — Integracao dos tres fluxos

- Login: reserva antes da verificacao Argon2; 5 tentativas por identificador
  e 40 por origem em 60 s. Conta tentativas bem-sucedidas tambem, sem reset
  imediato, para evitar corridas. Username e email sao chaves distintas.
- Cadastro: 12 por origem, 3 por email em 900 s.
- Solicitacoes de recuperacao e confirmacao compartilham 15 por origem e
  3 por email em 900 s. Resposta generica preservada.
- 429 com Retry-After restante; falha de banco ou segredo insuficiente
  resulta em 503, sem permitir tentativa desprotegida.
- Origem: somente request.client, nunca X-Forwarded-For lido diretamente.
  Next.js usa chamadas servidor-servidor; os usuarios compartilham o limite
  de origem do Next ate configurar um ingresso confiavel. Antes de publicar,
  definir arquitetura de proxy, restringir acesso direto a API e validar
  spoofing e isolamento de IP real ponta a ponta. Nao confiar em todos os proxies.
- RATE_LIMIT_SECRET opcional, fallback JWT_SECRET; chave dedicada na publicacao.
- Limpeza: python -m backend.scripts.limpar_limites (simulacao);
  --executar remove somente expirados. Agendar periodicamente na hospedagem
  e configurar limites de ingresso para limitar crescimento sob abuso.
- Confirmacao e redefinicao de tokens de alta entropia, mudanca/exclusao de
  conta autenticada e demais rotas ficam fora deste incremento.

## F11.3 — Autenticacao e permissoes

- Validacao rigorosa dos tokens JWT.
- Politica de confirmacao de email aplicada
  tambem nas sessoes existentes.
- Rate limiting compartilhado entre alteracao
  de senha e exclusao de conta.
- Limite de 5 tentativas por usuario em 300 s.
- Tratamento de HTTP 429 no frontend.
- 268 testes aprovados, 8 ignorados localmente.
- ESLint e TypeScript aprovados.
- Nenhuma migration adicional.
- Nenhum deploy realizado.

