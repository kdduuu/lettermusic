# Lettermusic — Mapa de telas e API da V1

## Páginas principais

| Página | Caminho | Responsabilidade |
|---|---|---|
| Descobrir | `/` | Indicadores e álbuns em destaque |
| Buscar | `/buscar` | Artistas, álbuns e faixas |
| Álbuns | `/albuns` | Exploração de álbuns |
| Álbum | `/albuns/[id]` | Detalhe e interações |
| Artista | `/artistas/[id]` | Discografia e informações |
| Reviews | `/reviews` | Feed público |
| Listas pessoais | `/listas` | Criar e gerenciar |
| Explorar listas | `/listas/explorar` | Listas públicas e autoria |
| Detalhe de lista | `/listas/[id]` | Itens e edição autorizada |
| Biblioteca | `/biblioteca` | Registros paginados |
| Comunidade | `/comunidade` | Atividade social |
| Perfil | `/usuarios/[username]` | Perfil público |
| Conta | `/conta` | Nome, senha, e-mail, exclusão |

## Fluxos de apoio

- `/cadastro` e `/entrar`
- `/esqueci-senha` e `/redefinir-senha`
- `/reenviar-confirmacao` e `/confirmar-email`

## Contratos importantes

- `GET /catalogo/buscar`
- `GET /catalogo/musicbrainz/{id}/...`
- `GET /descoberta/...`
- `GET /social/reviews`
- `GET /social/comunidade`
- `GET /usuarios/{username}/social`
- `GET /listas/publicas`
- `GET /listas/minhas`
- `GET /listas/{lista_id}`
- `GET /interacoes/escutas`
- `GET /interacoes/avaliacoes`
- `GET /interacoes/reviews`
- `GET /biblioteca/favoritos`
- `GET /biblioteca/quero-ouvir`
- `GET /auth/conta`
- `PATCH /auth/conta`
- `POST /auth/senha`
- `DELETE /auth/conta`
- `POST /auth/senha/solicitar`
- `POST /auth/senha/redefinir`
- `POST /auth/email/solicitar`
- `POST /auth/email/confirmar`

A documentação OpenAPI é a fonte completa de métodos e schemas.

## Regras de interface

- Exibir falha de conexão separadamente de resultado vazio.
- Nenhuma página pública deve expor e-mail privado.
- Não mostrar listas privadas de outros usuários.
- Excluir review não remove escutas e avaliações.
- Biblioteca pagina categorias separadamente.
- Informações de popularidade devem vir de dados reais.
- Membros ativos não significam usuários online agora.
- Não apresentar streaming ou funções futuras como ativas.

## Referências visuais

As telas de Perfil e Detalhes de Lista são referências
prioritárias. Preservar sua composição durante a F09.

A Comunidade V1 permanece simples, sem novos módulos sociais.
