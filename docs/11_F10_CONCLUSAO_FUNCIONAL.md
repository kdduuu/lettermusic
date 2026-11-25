# F10 — Conclusao funcional antes da publicacao

F10.1: main consolidada via PR #14, com a identidade visual aprovada e CI frontend verde. Historico preservado.

## F10.2 — Quatro favoritos do perfil

- Selecao publica de 0 a 4 albuns distintos, manual e ordenada. Nenhum titulo visivel no perfil; capas livres e lapis apenas para o dono. Visitantes sem selecao nao veem espacos vazios.
- PUT /auth/perfil/favoritos: { "albuns": [MBID, ...] }. Substituicao atomica; autenticacao define o dono. GET /usuarios/{username}/social adiciona albuns_favoritos.
- MusicBrainz fornece metadados oficiais; apenas tipo Album. Nao cria escuta, avaliacao, review, marcador de ouvido nem favorito privado. Selecao pode ser limpa.
- Migration f10a2c9e014f sobre d85c2b9e014f. Banco de desenvolvimento: alembic upgrade head. Nunca aplicar em producao sem backup e revisao.
- Testes: autenticacao, isolamento, limite, duplicidade, ordem, limpeza, rollback e tipo de obra. CI deve executar migracoes e testes existentes.
- Validar no navegador: pesquisa, adicionar ate quatro, remover, reordenar, salvar, recarregar, visitar deslogado e confirmar que Library e History nao mudaram.

## Restante antes de publicar

1. Discografia: ordenacao global, paginacao e classificacoes oficiais.
2. Diagnosticar 1 Issue do Next.js com mensagem real; nao ocultar.
3. Revisar fluxos sociais, conta, emails, privacidade, seguranca, desempenho, mobile e legibilidade. Testar volumes e estados vazios.
4. Revisar documentacao, variaveis de ambiente, configuracao de deploy, backup, HTTPS e custos.

Nenhum deploy nesta etapa. Nao considerar pronto para producao ate F11/F12.
