# LETTERMUSIC — Referência visual AOTY / F09.6
Data: 24/11/2026

## Fonte principal
https://www.albumoftheyear.org/ — Album of the Year (AOTY).

O AOTY era nossa principal referência de front-end desde o planejamento. Não deve ser omitido em análises futuras. As inspirações secundárias são Letterboxd (social), Rate Your Music (catálogo/opiniões), Last.fm (histórico), Goodreads (coleções) e Discogs (fichas).

## O que extraímos do AOTY
- Alto aproveitamento da área útil: capas próximas, informações logo abaixo, boa densidade e ritmo editorial.
- Tipografia de leitura compacta e números/avaliações alinhados às obras.
- Filtros e controles ocupando pouco espaço, sem enunciados que expliquem o óbvio.
- Fichas de álbum articulando capa, detalhes, tracklist e percepção da comunidade.
- Reviews centradas em pessoas, notas reais e textos; não inventar notas de críticos.

## Decisões da F09.6
1. Escala visual de desktop ajustada via CSS para 100% do navegador, sem zoom global nem exigir 80% manual.
2. Grades de até cinco capas no catálogo desktop, preservando respiro e layouts móveis.
3. Remover a busca duplicada da abertura da Descobrir; manter busca global do cabeçalho.
4. Destacar na abertura um álbum real que não repita os mais ouvidos, quando houver.
5. Não exibir "Mais bem avaliados" na home quando os registros forem muito poucos ou não houver diversidade de notas.
6. Exibir exclusivamente avaliações reais dos usuários no sistema 0,5–5,0; não fabricar notas de críticos, tendências ou outros dados.
7. Proteger o estilo grafite e as capas editoriais autorais das listas. Preservar sem streaming.
8. Manter Perfil e Lista detalhada como referências internas muito importantes; corrigir proporções sem perder presença.
9. Só texto necessário: rótulos acessíveis, estados vazios, detalhes e ações; não usar slogans/legendas redundantes.

## Onde pesquisar novamente
- Home https://www.albumoftheyear.org/
- Descoberta https://www.albumoftheyear.org/discover/
- Avaliações de usuários https://www.albumoftheyear.org/user-reviews/popular/
- Álbuns https://www.albumoftheyear.org/ratings/user-highest-rated/2026/
- Listas https://www.albumoftheyear.org/lists.php
- Fichas e perfis: seguir links do site; algumas rotas podem bloquear requisições automatizadas.

## Limites importantes
AOTY é inspiração estrutural/estética, não cópia de interface ou conteúdo. O Lettermusic continua uma rede social musical que registra escuta, avaliações, reviews e listas. Não implementamos reprodução musical, notas de críticos, métricas não existentes, rankings artificiais nem integrações com serviços externos para reproduzir faixas.

## Validação
Revisar em desktop com zoom 100%, além de pelo menos um viewport estreito. Testar de verdade: Descobrir, catálogo, álbum e tracklist/modal, Reviews, Listas, Comunidade, Perfil, Biblioteca e login. GitHub Actions ESLint, TypeScript e build não comprovam fidelidade visual. Branch F09.6 separada; nunca mesclar na main antes de aprovação visual.
