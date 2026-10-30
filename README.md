
# Lettermusic

Rede social de música em desenvolvimento, inspirada na ideia de registrar e compartilhar experiências musicais.

O projeto permite pesquisar álbuns, EPs e singles, registrar escutas, avaliar obras, publicar reviews e organizar coleções pessoais.

**Não é um serviço de streaming.**

Atualmente, o projeto possui um backend funcional em Python/FastAPI. A interface web ainda não foi desenvolvida.

## Estado do projeto

### Etapas concluídas

- **Sprint 00 — Estrutura inicial:** ambiente Python, FastAPI, Git, testes e integração com MusicBrainz.
- **Sprint 01 — Catálogo:** PostgreSQL, modelo de obras, migrações Alembic e persistência de dados.
- **Sprint 02 — Usuários:** cadastro, autenticação JWT, senhas protegidas por hash e perfis públicos.
- **Manutenção técnica:** melhorias nas transações do banco, metadados de artistas e validação dos tokens.
- **Sprint 03 — Interações musicais:** obras ouvidas, escutas repetidas, avaliações de 0,5 a 5 estrelas, médias e reviews.
- **Sprint 04 — Biblioteca pessoal:** favoritos e lista Quero ouvir, com adição, consulta e remoção de obras.

### Próximas etapas

- Listas musicais personalizadas.
- Recursos de descoberta e interação social.
- Ampliação do catálogo e dos metadados.
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

## Regras importantes

- Pesquisar no MusicBrainz não cadastra automaticamente uma obra.
- O cadastro local acontece quando uma interação relevante precisa persistir a obra.
- Marcar uma obra como ouvida não cria uma escuta com data.
- Registrar uma avaliação ou publicar uma review cria uma escuta.
- Editar ou excluir uma review não altera o histórico de escutas.
- Adicionar ou remover favoritos e itens de Quero ouvir não cria nem exclui escutas.
- Uma obra pode estar simultaneamente em Favoritos e Quero ouvir.
- Cada usuário gerencia apenas suas próprias coleções.

As operações que alteram múltiplos registros devem utilizar transações consistentes. A função `registrar_obra()` não confirma a transação diretamente.

## Endpoints da biblioteca

| Método | Endpoint | Descrição |
|---|---|---|
| POST | `/biblioteca/favoritos` | Adicionar favorito |
| GET | `/biblioteca/favoritos` | Consultar favoritos |
| DELETE | `/biblioteca/favoritos/{obra_id}` | Remover favorito |
| POST | `/biblioteca/quero-ouvir` | Adicionar a Quero ouvir |
| GET | `/biblioteca/quero-ouvir` | Consultar Quero ouvir |
| DELETE | `/biblioteca/quero-ouvir/{obra_id}` | Remover de Quero ouvir |

Todos os endpoints da biblioteca exigem autenticação JWT.

Os demais endpoints podem ser consultados na documentação interativa do FastAPI.

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

**Checkpoint da Sprint 04:** 55 testes automatizados aprovados, incluindo 11 testes específicos da biblioteca musical.

Os testes automatizados utilizam um banco SQLite temporário. As funcionalidades também foram validadas manualmente no PostgreSQL local pelo Swagger.

## Segurança

- Senhas de usuários são armazenadas com hash, não em texto puro.
- Operações privadas exigem autenticação JWT.
- As consultas e alterações das coleções são vinculadas ao usuário autenticado.
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

**Backend em desenvolvimento — Sprint 04 concluída funcionalmente.**

Próximo objetivo: continuar a construção das funcionalidades sociais do Lettermusic, mantendo escopo reduzido, testes automatizados e organização do código.
