# Lettermusic — Estado atual da V1

**Checkpoint:** F08.6C2, em validação.
**Fonte da verdade:** código, testes e GitHub.

## O que estamos construindo

Uma plataforma social para registrar e compartilhar experiências
musicais. Não reproduz música e não é um serviço de streaming.

O foco de aprendizado é backend, arquitetura, API, contratos,
persistência e manutenção. O frontend deve ser funcional,
consistente e visualmente agradável, sem complexidade excessiva.

## Stack confirmada

- Next.js, React, TypeScript e CSS Modules.
- FastAPI, SQLAlchemy, Alembic e PostgreSQL.
- MusicBrainz, Cover Art Archive e ListenBrainz opcional.
- Pytest, ESLint, TypeScript e GitHub Actions.

## Decisões preservadas

- MusicBrainz como fonte única de catálogo na V1.
- Nenhum cadastro manual próprio de álbuns na V1.
- Busca sem persistência automática.
- Já ouvi distinto de múltiplas escutas.
- Avaliação e review únicas por usuário/obra, editáveis.
- Criar avaliação ou review registra uma escuta.
- Favoritos, Quero ouvir e listas não implicam escuta.
- Listas públicas e privadas, com autorização por proprietário.
- Telas de Perfil e Detalhes de Lista como referências visuais.
- F09 reservada ao refinamento visual.
- F10 reservada à infraestrutura e publicação.

## Fases

- F01–F08.5: funcionalidades centrais implementadas.
- F08.6A: API de listas públicas e revogação de links.
- F08.6B: interface de listas, reviews, Biblioteca e busca.
- F08.6C1: proteções de conta e limpeza de tokens.
- F08.6C2: documentação, teste de paginação e auditoria final.
- F09: acabamento visual.
- F10: implantação, validação e publicação.

A F08.6 só estará encerrada após testes e commit aprovado.

## Diretrizes visuais

Fluidez, conteúdo centralizado, música em destaque, poucos
elementos, tipografia editorial, cores discretas e experiência
social evidente. Preservar as referências aprovadas.

## Próximo passo

Validar a F08.6C2, revisar `git diff`, publicar o checkpoint e
iniciar o planejamento visual da F09.
