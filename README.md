# Lettermusic

Rede social de música para descobrir álbuns, registrar escutas,
avaliar, escrever reviews e compartilhar listas. Inspirada em
diários culturais como o Letterboxd. **Não é streaming.**

**Status:** aplicação funcional em desenvolvimento local.
F08.6 em fechamento; refinamento visual (F09) e publicação
(F10) ainda pendentes. Não considerada pronta para produção.

## Tecnologias

- Backend: Python 3.14, FastAPI, Pydantic, JWT e Argon2.
- Banco: PostgreSQL, SQLAlchemy, Psycopg e Alembic.
- Frontend: Next.js 16, React, TypeScript e CSS Modules.
- Integrações: MusicBrainz, Cover Art Archive e ListenBrainz
  opcional para indicadores de popularidade.
- Qualidade: pytest, ESLint, TypeScript, build e GitHub Actions.

## Funcionalidades

- Cadastro, login, logout, gerenciamento e exclusão de conta.
- Verificação de e-mail e recuperação de senha por link temporário.
- Busca de artistas, álbuns e faixas pelo MusicBrainz.
- Páginas de álbum e artista com metadados reais.
- Marcação Já ouvi e histórico de múltiplas escutas.
- Avaliações de 0,5 a 5 estrelas, em passos de 0,5.
- Reviews criadas, editadas e excluídas pelo próprio autor.
- Favoritos e Quero ouvir.
- Biblioteca com paginação por categoria.
- Listas públicas e privadas, edição e ordenação.
- Exploração de listas públicas e identificação do autor.
- Perfis públicos, feed de reviews, descoberta e Comunidade.

## Regras de negócio

1. Pesquisar não persiste uma obra no banco.
2. A persistência acontece quando houver interação.
3. O MusicBrainz é a fonte de identificação das obras.
4. Já ouvi é único por usuário/obra; escutas podem ser múltiplas.
5. Avaliar ou publicar review cria escuta; editar não cria outra.
6. Favoritar e adicionar a listas não registra escuta.
7. Uma avaliação e uma review por usuário/obra; ambas editáveis.
8. Listas privadas ficam acessíveis somente ao proprietário.
9. Dados pessoais não entram nas respostas públicas dos perfis.

Obras não encontradas podem ser adicionadas ao MusicBrainz.
A V1 não oferece cadastro manual independente de catálogo.

## Executar localmente

Na raiz, com Python e PostgreSQL instalados:

```powershell
py -3.14 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

Copie `.env.example` para `.env`, preenchendo os dados do
PostgreSQL e um `JWT_SECRET` forte. Mantenha o `.env` privado.

Inicie o backend:

```powershell
python -m alembic upgrade head
python -m uvicorn backend.app.main:app --reload
```

API: http://127.0.0.1:8000
OpenAPI: http://127.0.0.1:8000/docs

Em outro terminal, inicie o frontend:

```powershell
cd frontend
npm ci
npm run dev
```

Interface: http://localhost:3000

O servidor Next.js consulta a API por meio de `BACKEND_URL`,
cujo padrão local é `http://127.0.0.1:8000`.
A variável é usada no servidor, não em `NEXT_PUBLIC_*`.

### E-mails

Para testar recuperação e verificação, configure no `.env`:

- `EMAIL_BASE_URL`
- `EMAIL_REQUIRE_VERIFICATION`
- `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`
- `SMTP_PASSWORD`, `SMTP_FROM`, `SMTP_SSL`

No desenvolvimento, a verificação obrigatória pode ficar
desativada. Para publicação, deve ser ativada e validada.

A configuração SMTP local não deve ser copiada para o Git.

## Testes

Backend:

```powershell
python -m pytest backend/tests -q
```

Frontend:

```powershell
cd frontend
npm run lint
npm run build
npx tsc --noEmit
```

Testes rápidos usam SQLite isolado e MusicBrainz simulado.
Quatro testes PostgreSQL locais são ignorados quando
`LETTERMUSIC_TEST_DATABASE_URL` não está configurada.

Os workflows GitHub Actions executam testes e verificações
em ambiente descartável. O sucesso local não substitui
testes reais da aplicação publicada.

### Limpeza administrativa de tokens

Simulação, sem excluir registros:

```powershell
python -m backend.scripts.limpar_tokens_conta
```

Execução de limpeza:

```powershell
python -m backend.scripts.limpar_tokens_conta --executar
```

O agendamento dessa rotina pertence à configuração de produção.

## Preparação para publicação

Ainda necessários: hospedagem HTTPS, segredos seguros, proteção
compartilhada contra abuso, e-mail confiável, backups, logs,
monitoramento, revisão de privacidade e testes ponta a ponta.

**Não publicar com o `.env` de desenvolvimento.**

## Repositório

https://github.com/kdduuu/lettermusic
