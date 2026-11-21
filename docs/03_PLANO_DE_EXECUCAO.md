# Lettermusic — Plano de execução

## Método de aprendizado

Lógica → Sintaxe → Motivo → Aplicação.

Cada etapa deve ter escopo controlado, testes e checkpoint
antes de publicar. Evitar reformulações desnecessárias.

## Histórico resumido

- F01: fundação Next.js e integração inicial com FastAPI.
- F02: busca, detalhes, artistas e capas.
- F03–F05: autenticação, interações e biblioteca.
- F06–F07: listas, perfis, reviews e Comunidade.
- F08.4: exploração, popularidade e estabilidade.
- F08.5A: gerenciamento de conta e sessões.
- F08.5B: recuperação de senha e confirmação de e-mail.
- F08.6A: listas públicas e revogação de links.
- F08.6B: exploração, exclusão de reviews e paginação.
- F08.6C1: cadastro, login, tokens e exclusão de conta.
- F08.6C2: documentação e revisão final em validação.

## F09 — Refinamento visual

- Comparar telas reais com referências aprovadas.
- Padronizar tipografia, cores, espaçamento e componentes.
- Melhorar estados de erro, vazio, carregamento e foco.
- Conferir responsividade, navegação por teclado e contraste.
- Preservar a música como protagonista.
- Não refazer a arquitetura nem criar funcionalidades sociais.

## F10 — Publicação

- Selecionar hospedagem compatível com FastAPI e Next.js.
- Configurar PostgreSQL de produção e migrações.
- HTTPS, cookies seguros, variáveis e segredos protegidos.
- Verificação obrigatória de e-mail e envio confiável.
- Proteção distribuída contra abuso e criação massiva.
- Backups com restauração testada.
- Limpeza periódica de tokens.
- Logs, erros, monitoramento e alertas.
- Política de privacidade e canal de solicitações de dados.
- Procedimento para conteúdo inadequado.
- Testar cadastro, login, recuperação e interações no ar.
- Validar custos e funcionamento após reinicialização.

## Critério de conclusão da V1

Funcionalidades centrais aprovadas, interface refinada,
testes verdes, publicação segura e documentação suficiente
para outra pessoa executar ou manter a aplicação.

## Regras de entrega

Manter histórico Git, validar antes de commitar e nunca
versionar `.env`, senhas, tokens ou dados privados.
