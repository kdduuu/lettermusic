# F09.13 — Consolidação editorial

Base: F09.12. Direção aprovada por conversa em 24/11/2026: AOTY (organização e densidade), Spotify (fluidez, não reprodução), revistas editoriais (composição e personalidade), Corinthians Archive Studies (identidade própria).

- Inglês como idioma único da interface V1; nomes técnicos, URLs internas, contratos e banco permanecem inalterados. Conteúdo do usuário e metadados musicais não são traduzidos.
- Discover: quatro seções (abertura/Featured, Most played, Reviews, Lists). Remover ranking condicional extra e divisórias entre seções. Preservar seleção real e evitar textos de preenchimento.
- Library: categoria ativa com URL e paginação; uma requisição de registros por vez. Capas para Listened, Favorites, Want to listen e Ratings; diário com miniaturas para History e Reviews. Sem duplicação da vitrine e sem seis listas verticais.
- Albums: estrutura visual aprovada, preservada. Album detail: retirar título visual redundante da tracklist, manter nome acessível Tracks.
- Profile, Reviews, Lists, Community, Search, Artist, login e conta: preservar estruturas, traduzir textos de interface, erros e ações. Não inventar dados.
- README inglês complementar; documentação técnica existente em português.

## Limites
Não há alterações no FastAPI ou no banco. E-mails transacionais do backend e traduções de mensagens de validação nativas dependem de revisão separada. Quatro favoritos públicos, ordenação global de discografia e indicador Next.js pendentes. Validar CI, fluxo de autenticação, biblioteca e navegação em desktop/mobile antes de merge. Não considerar resultado visual aprovado até conferir no navegador.
