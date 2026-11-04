# Lettermusic

Rede social para descobrir música, registrar escutas, avaliar álbuns, escrever reviews e montar listas pessoais. Inspirada na ideia de um diário musical; **não é um serviço de streaming**.

**Status:** backend funcional para desenvolvimento e integração com o frontend. A interface web ainda será construída. Este projeto não deve ser considerado pronto para produção pública sem revisão de segurança e implantação.

## Tecnologias

- **API:** Python 3.14, FastAPI, Pydantic, JWT e hash Argon2 (`pwdlib`).
- **Persistência:** PostgreSQL, SQLAlchemy, Psycopg e Alembic.
- **Catálogo externo:** MusicBrainz (obras identificadas por *release-group MBID*).
- **Qualidade:** pytest (SQLite isolado nos testes rápidos; PostgreSQL dedicado na integração) e GitHub Actions.

## Funcionalidades do backend

| Área | Comportamento |
| --- | --- |
| Catálogo | Busca no MusicBrainz; cadastro local somente quando houver interação; metadados oficiais |
| Contas | Cadastro, login JWT, consulta de conta e perfis públicos |
| Escutas | Marcação **Já ouvi** distinta de múltiplas escutas |
| Avaliações | Uma avaliação atual de 0,5 a 5, editável; média da comunidade |
| Reviews | Uma review por usuário e obra, editável; publicar registra escuta |
| Biblioteca | Favoritos e **Quero ouvir**, independentes |
| Listas | Públicas/privadas, itens ordenados e controle de acesso pelo proprietário |
| Descoberta | Obras mais ouvidas e mais bem avaliadas |
| Social | Perfil público, estatísticas, reviews e listas públicas recentes |

### Regras de integridade

- A busca no MusicBrainz **não** cadastra a obra automaticamente.
- Ao criar uma interação, o cliente pode enviar apenas `id_musicbrainz`: o servidor consulta os metadados oficiais quando necessário.
- Registrar uma avaliação ou publicar uma review cria uma escuta. Editá-las não cria escuta adicional.
- Marcar **Já ouvi** não cria uma escuta. Favoritos, Quero ouvir e listas também não criam escutas.
- Exclusão de favorito ou item de lista não exclui a obra do catálogo nem o histórico de escutas.
- Regras de unicidade são protegidas no banco. Operações que afetam vários registros preservam transações.
- Listas privadas e dados pessoais não são expostos nos endpoints públicos.

## Executar localmente (Windows / PowerShell)

Na raiz do repositório:

```powershell
py -3.14 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

Configure `.env` copiando `.env.example` e preenchendo credenciais **locais** do PostgreSQL e uma chave JWT aleatória de pelo menos 32 caracteres. **Não publique `.env`, senhas ou tokens.**

```powershell
python -m alembic upgrade head
python -m uvicorn backend.app.main:app --reload
```

A API ficará em `http://127.0.0.1:8000` e a documentação interativa em `http://127.0.0.1:8000/docs`. A documentação OpenAPI completa permanece no Swagger.

### Exemplos de requisições

Pesquisar: `GET /catalogo/buscar?termo=Kid%20A&artista=Radiohead`.

Favoritar (exige JWT): `POST /biblioteca/favoritos` com corpo:

```json
{
  "obra": {
    "id_musicbrainz": "b1392450-e666-3926-a536-22c65f834433"
  }
}
```

Para consultar resultados paginados, use, por exemplo, `GET /catalogo/obras?pagina=2&por_pagina=10`. Nas listas de interações, o backend devolve também metadados da obra para facilitar as telas.

O CORS é configurado por `CORS_ORIGINS` (origens separadas por vírgula). Em desenvolvimento, as origens padrão são `http://localhost:5173` e `http://127.0.0.1:5173`. **CORS não substitui autenticação ou autorização.**

## Testes

### Testes rápidos

```powershell
python -m pytest backend/tests -q
```

Os testes comuns usam banco SQLite isolado e simulam consultas ao MusicBrainz, evitando alterar o PostgreSQL de desenvolvimento.

### Integração real com PostgreSQL

O arquivo `backend/tests/test_integracao_postgresql.py` testa criação simultânea de obras, marcações **Já ouvi**, conflito de favoritos e rollback com conexões reais.

Por segurança, esses testes **são ignorados** se `LETTERMUSIC_TEST_DATABASE_URL` não estiver configurada. Eles **recusam bancos cujo nome não termine em `_test`**, e criam/removem apenas um *schema* temporário por teste. Não reutilize sua base de desenvolvimento como base de testes.

Exemplo para uma conta PostgreSQL de testes já criada e autorizada a criar schemas:

```powershell
$env:LETTERMUSIC_TEST_DATABASE_URL = "postgresql+psycopg://USUARIO:SENHA@localhost:5432/lettermusic_test"
python -m pytest backend/tests/test_integracao_postgresql.py -q
Remove-Item Env:\LETTERMUSIC_TEST_DATABASE_URL
```

Substitua usuário e senha pelos valores de uma conta **exclusiva de testes**, nunca aponte para `lettermusic_dev`. Se a senha tiver caracteres especiais, codifique-os corretamente na URL.

### CI — GitHub Actions

O workflow `.github/workflows/backend.yml` executa testes automaticamente em alterações relevantes. Ele cria um **PostgreSQL descartável no próprio runner**, aplica as migrações Alembic e executa os testes rápidos e reais, sem acessar o seu computador ou seus bancos.

No GitHub, confira **Actions → Backend - Testes** depois de publicar o workflow. O backend só será considerado **validado para iniciar o frontend** após uma execução verde no GitHub e uma revisão do resultado.

## Dependências e manutenção

`requirements.txt` conserva as versões fixadas no ambiente funcional. Alterações ou atualizações devem acontecer em um commit próprio, seguidas de testes completos. O aviso conhecido `StarletteDeprecationWarning` não impede a execução da suíte atual e não deve motivar uma atualização às cegas.

### O que fica fora do escopo desta fase

A estrutura está preparada para começar a interface. Para colocar o serviço em produção pública serão necessárias medidas adicionais: hospedagem HTTPS, gestão de segredos, recuperação de conta, proteção contra abuso e tentativas repetidas de login, estratégia de backups e monitoramento.

## Repositório

Desenvolvimento educacional e de portfólio: [kdduuu/lettermusic](https://github.com/kdduuu/lettermusic).
