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
