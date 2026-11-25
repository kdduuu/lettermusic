# F09.12 — refinamento de fechamento

Base: F09.11 (02ad1e7). Preservar grafite, títulos serifados, acento rosa discreto, escala compacta em zoom 100%, capas reais dos álbuns e arte LM. das listas sem geometria.

## Revisão e alterações
- Descobrir: manter abertura aprovada; acrescentar até três listas públicas reais, sem conteúdo fictício.
- Álbum: navegação contextual, card de faixa com álbum/duração e colunas fixas, estados ativos dos registros sem mudar regras.
- Catálogo e busca: metadados mais legíveis, mensagens concisas; manter filtros nativos e melhoria progressiva do menu.
- Artista: voltar à busca, metadados legíveis; preservar inicial única.
- Reviews, Comunidade e Perfil: texto secundário legível e quebra de conteúdo longo.
- Listas: preservar arte e layout; navegação de detalhe para listas, legibilidade.
- Biblioteca: distinguir falha de consulta de coleção vazia; reduzir caixas, preservar navegação e registros privados.
- Autenticação/conta: controles legíveis; manter avisos de segurança e recuperação.
- Cabeçalho: rota ativa sem depender de hover, foco de teclado e navegação móvel.

## Pendências funcionais (não mascarar como concluídas)
- Quatro favoritos públicos: seleção explícita independente, ordenação manual, até quatro; não expor favoritos da biblioteca. Requer contrato, armazenamento e testes de autorização/privacidade próprios.
- Discografia: ordenação atual é por página; validar e resolver ordenação global no contrato de catálogo, não esconder a limitação.
- Indicador Next.js 1 Issue dos prints: causa não confirmada sem log local.
- CI, responsividade real, regressão funcional e aprovação visual: pendentes no momento desta alteração.

## Critério de encerramento
Na raiz: `python -m pytest backend/tests -q`, `git diff --check`.
No frontend: `npm run lint`, `npx next typegen`, `npx tsc --noEmit`, `npm run build`.
Verificar navegação por teclado e larguras 360, 768 e desktop 100%; fluxos de login, busca, registros, review, lista pública/privada, biblioteca e perfil. Não exigir novos prints de todas as telas. Só reabrir design diante de defeitos reproduzíveis. Não publicar ou fazer merge antes de validar.
