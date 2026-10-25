# Lettermusic

Rede social de musica em desenvolvimento: catalogo de albuns, EPs e singles,
registro de escutas, notas, reviews, favoritos e listas. **Nao e um servico de streaming.**

## Estado atual

- Sprint 00: ambiente FastAPI, Git, testes e integracao MusicBrainz.
- Sprint 01: modelo `Obra`, migracoes, PostgreSQL e consulta do catalogo pela API.
- Sprint 02: cadastro de usuarios, login JWT e perfis publicos.
- Manutencao: artista persistido no catalogo, operacoes de banco com transacoes
  controladas pelo chamador e testes reforcados de tokens JWT.
- Proxima sprint: obras ouvidas, escutas, avaliacoes e reviews.

## Tecnologias

Python, FastAPI, PostgreSQL, SQLAlchemy, Alembic, Psycopg,
PyJWT, pwdlib/Argon2 e pytest.

## Iniciando localmente (Windows / PowerShell)

1. Ative o ambiente virtual existente: `.\.venv\Scripts\Activate.ps1`.
2. Instale as dependencias: `python -m pip install -r requirements.txt`.
3. Configure o `.env` privado com base no `.env.example`, usando credenciais locais.
4. Execute migracoes: `python -m alembic upgrade head`.
5. Inicie a API: `python -m uvicorn backend.app.main:app --reload`.
6. Abra `http://127.0.0.1:8000/docs`.
7. Testes: `python -m pytest backend/tests -v`.

Para atualizar os metadados da obra de exemplo ja cadastrada:
`python -m backend.scripts.demo_catalogo`.

## Seguranca e compartilhamento

- Nunca publique o `.env`, chaves JWT, senhas reais ou tokens de acesso.
- A chave `JWT_SECRET` e a senha do banco ficam somente no `.env` local.
- Para gerar um ZIP apenas dos arquivos **versionados**, apos fazer commit:
  `git archive --format=zip --output=lettermusic_codigo.zip HEAD`
- Nao envie pastas `.git`, `.venv` ou arquivos `.env` em pacotes de revisao.
- Este e um MVP em desenvolvimento: antes de publicar para terceiros,
  ainda serao necessarios controle de tentativas de login, HTTPS,
  gestao de sessoes e recuperacao de conta.

## Regra de catalogo

Consultar o MusicBrainz nao cadastra obras automaticamente.
A persistencia deve acontecer quando houver uma interacao relevante.
Uma operacao de negocio (obra + interacao) deve ser confirmada
em uma unica transacao; `registrar_obra()` nao chama `commit()`.
