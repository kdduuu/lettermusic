# Lettermusic — Próxima sessão: começar o front-end sem se perder

## Onde paramos

- Stack V1 **confirmada**: Next.js (App Router) + React + TypeScript + CSS Modules; FastAPI/SQLAlchemy/Alembic/PostgreSQL preservados.
- Ainda **não** criamos `frontend/`, nem instalamos pacotes, nem modificamos o projeto por causa deste planejamento.
- Snapshot recebido: `main...origin/main` limpo; commit `0e7c598`; 130 testes aprovados, 4 ignorados, 1 aviso no computador do autor.
- 7 telas aprovadas; Comunidade tem referência V1 simplificada. Sem novas rodadas de prototipação como bloqueio.
- Foco de aprendizado: back-end, requisições, estrutura e manutenção; front-end necessário/suficiente.

## Primeiros comandos no PowerShell (na raiz do projeto)

```powershell
git status -sb
git log -1 --oneline
node --version
npm --version
```

**Não executar** comandos de criação/instalação antes de conferir versões e caminho correto. O próximo passo prático será inicializar `frontend/` com o instalador oficial do Next.js, em configuração pequena e auditável.

## Primeira entrega que queremos alcançar

1. `frontend/` criado e executando localmente.
2. Cabeçalho, tipografia e cores base do Lettermusic sem excesso de estilização.
3. Uma requisição real (`/health` ou busca pública) saindo do Next.js e chegando ao FastAPI.
4. Estados de carregamento e erro; CORS ajustado para origem da aplicação quando necessário.
5. Teste manual comprovado e checkpoint antes do primeiro commit dessa etapa.

## Atenção

- API local: `http://127.0.0.1:8000`, documentação em `/docs`.
- Next.js usa usualmente a porta `3000`, enquanto CORS existente estava preparado para `5173` (Vite). Ajustar a variável `CORS_ORIGINS` localmente se o navegador acessar API diretamente.
- Não copiar `.env` real para o front-end ou para ZIPs; `NEXT_PUBLIC_*` é público.
- Antes da autenticação, decidir política de sessão segura e tratamento do JWT com vencimento; não salvar credenciais improvisadamente no navegador.
- Não construir a Comunidade antes de termos rotas reais para o feed.

## Mensagem pronta para abrir a sessão seguinte

> Vamos iniciar a primeira sprint do front-end do Lettermusic, seguindo o pacote `LETTERMUSIC_ORGANIZACAO_V1`. A stack aprovada é Next.js + React + TypeScript + CSS Modules, com FastAPI/PostgreSQL preservados. Quero um passo por vez, com explicações Lógica → Sintaxe → Motivo → Aplicação, especialmente requisições e arquitetura; não quero gastar tempo excessivo só no visual. Meu projeto local estava limpo no commit `0e7c598`, com 130 testes aprovados e 4 ignorados. Vamos começar verificando Node/npm, criando a estrutura mínima do Next.js e fazendo uma requisição real à API. Não mexa em vários arquivos sem necessidade.
