
# Lettermusic

Rede social de música em desenvolvimento, inspirada na ideia de registrar e compartilhar experiências musicais.

O projeto permite pesquisar álbuns, EPs e singles, registrar escutas, avaliar obras, publicar reviews e organizar coleções pessoais e listas musicais personalizadas.

**Não é um serviço de streaming.**

Atualmente, o projeto possui um backend funcional em Python/FastAPI. A interface web ainda não foi desenvolvida.

## Estado do projeto

### Etapas concluídas

- **Sprint 00 — Estrutura inicial:** ambiente Python, FastAPI, Git, testes e integração com MusicBrainz.
- **Sprint 01 — Catálogo:** PostgreSQL, modelo de obras, migrações Alembic e persistência de dados.
- **Sprint 02 — Usuários:** cadastro, autenticação JWT, senhas protegidas por hash e perfis públicos.
- **Manutenção técnica:** melhorias nas transações do banco, metadados de artistas e validação dos tokens.
- **Sprint 03 — Interações musicais:** obras ouvidas, escutas repetidas, avaliações de 0,5 a 5 estrelas, médias e reviews.
- **Sprint 04 — Biblioteca pessoal:** favoritos e Quero ouvir, com adição, consulta e remoção de obras.
- **Sprint 05 — Listas musicais:** listas públicas e privadas, inclusão e remoção de álbuns, organização de posições e controle de permissões.

### Próximas etapas

- Recursos de descoberta e interação social.
- Ampliação dos metadados apresentados pelo catálogo.
- Interface web integrada à API.
- Melhorias de segurança, testes e publicação.

## Tecnologias

- Python
- FastAPI
- PostgreSQL
- SQLAlchemy
- Alembic
- Psycopg
- Pydantic
- PyJWT
- pwdlib / Argon2
- pytest
- MusicBrainz API

## Funcionalidades disponíveis

### Catálogo

- Pesquisa de obras pelo MusicBrainz.
- Cadastro local de obras quando ocorre uma interação relevante.
- Consulta das obras armazenadas no PostgreSQL.

### Usuários

- Cadastro de contas.
- Login com token JWT.
- Consulta do próprio usuário autenticado.
- Consulta de perfis públicos.

### Interações musicais

- Marcar obras como ouvidas.
- Registrar múltiplas escutas da mesma obra.
- Consultar o histórico de escutas.
- Avaliar obras de 0,5 a 5 estrelas.
- Editar avaliações e consultar médias.
- Publicar, consultar, editar e excluir reviews.

### Biblioteca pessoal

- Adicionar e remover favoritos.
- Consultar favoritos do usuário autenticado.
- Adicionar e remover obras de Quero ouvir.
- Consultar a lista Quero ouvir.
- Impedir registros duplicados por usuário e obra.
- Manter as duas coleções independentes.

### Listas musicais personalizadas

- Criar listas com título e descrição opcional.
- Definir listas como públicas ou privadas.
- Consultar listas públicas sem autenticação.
- Consultar as próprias listas, incluindo as privadas.
- Editar informações e configurações de privacidade.
- Excluir listas próprias.
- Adicionar álbuns a listas existentes.
- Impedir a inclusão duplicada da mesma obra na mesma lista.
- Remover álbuns sem excluí-los do catálogo.
- Reorganizar a posição dos álbuns.
- Recalcular posições após a remoção de um item.
- Restringir modificações ao proprietário da lista.

## Regras importantes

### Catálogo e escutas

- Pesquisar no MusicBrainz não cadastra automaticamente uma obra.
- O cadastro local acontece quando uma interação relevante precisa persistir a obra.
- Marcar uma obra como ouvida não cria uma escuta com data.
- Registrar uma avaliação ou publicar uma review cria uma escuta.
- Editar ou excluir uma review não altera o histórico de escutas.
- Adicionar ou remover favoritos e itens de Quero ouvir não cria nem exclui escutas.
- Uma obra pode estar simultaneamente em Favoritos e Quero ouvir.

### Listas musicais

- As listas são públicas por padrão.
- O proprietário pode alterar a visibilidade posteriormente.
- Listas privadas não são disponibilizadas nos endpoints públicos.
- Somente o proprietário pode editar, excluir ou modificar os itens de sua lista.
- Uma obra pode participar de diferentes listas.
- A mesma obra não pode aparecer duas vezes na mesma lista.
- Adicionar ou remover uma obra de uma lista não registra nem exclui escutas.
- Remover uma obra da lista não exclui seu registro do catálogo.
- Excluir uma lista remove seus itens associados, preservando as obras do catálogo.
- As posições dos álbuns começam em 1 e são reorganizadas após movimentações e exclusões.

As operações que alteram múltiplos registros devem utilizar transações consistentes. A função `registrar_obra()` não confirma a transação diretamente.

## Endpoints

A documentação interativa completa está disponível no Swagger.

### Biblioteca pessoal

| Método | Endpoint | Descrição |
|---|---|---|
| POST | `/biblioteca/favoritos` | Adicionar favorito |
| GET | `/biblioteca/favoritos` | Consultar favoritos |
| DELETE | `/biblioteca/favoritos/{obra_id}` | Remover favorito |
| POST | `/biblioteca/quero-ouvir` | Adicionar a Quero ouvir |
| GET | `/biblioteca/quero-ouvir` | Consultar Quero ouvir |
| DELETE | `/biblioteca/quero-ouvir/{obra_id}` | Remover de Quero ouvir |

Todos os endpoints da biblioteca exigem autenticação JWT.

### Listas musicais

| Método | Endpoint | Descrição |
|---|---|---|
| POST | `/listas` | Criar lista |
| GET | `/listas/minhas` | Consultar minhas listas |
| GET | `/listas/minhas/{lista_id}` | Consultar minha lista, inclusive privada |
| GET | `/listas/{lista_id}` | Consultar lista pública |
| PUT | `/listas/{lista_id}` | Editar lista |
| DELETE | `/listas/{lista_id}` | Excluir lista |
| POST | `/listas/{lista_id}/itens` | Adicionar álbum |
| GET | `/listas/{lista_id}/itens` | Consultar itens de lista pública |
| GET | `/listas/minhas/{lista_id}/itens` | Consultar itens da minha lista |
| PATCH | `/listas/{lista_id}/itens/{obra_id}` | Alterar posição de álbum |
| DELETE | `/listas/{lista_id}/itens/{obra_id}` | Remover álbum |

As consultas públicas não exigem autenticação. As operações de gerenciamento e consultas privadas exigem JWT.

Nesta versão, os endpoints de itens retornam os identificadores das obras e suas posições. A apresentação visual dos metadados ficará para a integração com a interface web.

## Executando localmente

Requisitos: Python, PostgreSQL e ambiente de desenvolvimento configurado.

### 1. Ativar o ambiente virtual (Windows / PowerShell)

```powershell
.\.venv\Scripts\Activate.ps1
```

Se o ambiente ainda não existir, crie-o antes de ativar.

### 2. Instalar dependências

```powershell
python -m pip install -r requirements.txt
```

### 3. Configurar o ambiente

Crie seu arquivo `.env` com base em `.env.example` e configure as credenciais locais do PostgreSQL e a chave JWT.

Nunca publique o `.env` no repositório.

### 4. Aplicar as migrações

```powershell
python -m alembic upgrade head
```

### 5. Iniciar a API

```powershell
python -m uvicorn backend.app.main:app --reload
```

Swagger:

http://127.0.0.1:8000/docs

### 6. Executar os testes

```powershell
python -m pytest backend/tests -q
```

**Checkpoint da Sprint 05:** 66 testes automatizados aprovados, incluindo 11 testes específicos de listas musicais.

Os testes automatizados utilizam um banco SQLite temporário. As funcionalidades também foram validadas manualmente no PostgreSQL local pelo Swagger.

## Segurança

- Senhas de usuários são armazenadas com hash, não em texto puro.
- Operações privadas exigem autenticação JWT.
- Consultas e alterações das coleções pessoais são vinculadas ao usuário autenticado.
- Listas privadas não são expostas pelos endpoints públicos.
- Credenciais, tokens e configurações privadas não devem ser publicados.
- O arquivo `.env` deve permanecer fora do Git.

Este projeto ainda está em desenvolvimento. Antes de disponibilizá-lo publicamente para uso real, serão necessárias medidas adicionais de segurança, como HTTPS, proteção contra tentativas repetidas de login, gerenciamento de sessões e recuperação de contas.

## Compartilhamento do código

Para gerar um ZIP apenas dos arquivos versionados, depois de realizar o commit:

```powershell
git archive --format=zip --output=lettermusic_codigo.zip HEAD
```

Não inclua `.venv`, `.env` ou dados privados nos arquivos compartilhados.

## Status

**Backend em desenvolvimento — Sprint 05 concluída funcionalmente.**

O sistema já possui catálogo, usuários, autenticação, escutas, avaliações, reviews, biblioteca pessoal e listas musicais personalizadas.

Próximo objetivo: avançar nas funcionalidades sociais e na experiência de utilização, mantendo o escopo reduzido, os testes automatizados e a organização do código.
