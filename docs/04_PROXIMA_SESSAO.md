# Lettermusic — Próxima sessão

## Estado do projeto

F08.6C2 em validação. As principais funcionalidades já
estão implementadas; não é hora de ampliar o escopo.

A branch local contém alterações da F08.6 ainda não
publicadas. Não confundir o checkpoint local com o commit
anterior `b75c487`.

## Para encerrar a F08.6

Na raiz:

```powershell
python -m pytest backend/tests -q
git diff --check
git status -sb
```

No frontend:

```powershell
npm run lint
npm run build
npx tsc --noEmit
```

Verificar especialmente alterações de documentos e scripts
temporários. Publicar somente após validação.

## Próxima fase: F09

Revisão visual das telas já implementadas. Priorizar:

1. Descobrir e pesquisa.
2. Detalhes de álbum.
3. Perfil público.
4. Reviews e Comunidade.
5. Listas e detalhes de lista.
6. Biblioteca e telas de autenticação.
7. Responsividade, acessibilidade e pequenos estados.

A F09 não deve virar uma nova fase de desenvolvimento
de backend.

## Depois: F10

Publicação com hospedagem HTTPS, PostgreSQL seguro,
envio de e-mails confiável, proteção contra abuso, backup,
monitoramento e testes ponta a ponta em ambiente público.

## Lembretes

- Não usar `.env` real em ZIP ou commit.
- Não excluir a conta principal para testar o formulário.
- MusicBrainz permanece a fonte única de catálogo na V1.
- As telas aprovadas continuam sendo a referência visual.
