# Lettermusic — Ponto de partida V1

**Checkpoint:** 12/11/2026
**Situação:** fase visual encerrada para fins de execução; iniciando implementação de front-end em outra sessão. **Nenhum código foi modificado neste pacote.**

## Intenção do projeto

Plataforma **social de música**, inspirada no Letterboxd: descobrir, registrar escutas, avaliar, escrever reviews, organizar listas, explorar atividades. **Não é streaming**.

**Objetivo de aprendizado:** dar mais peso a **back-end, arquitetura, requisições, contratos de API, banco, testes e manutenção**. Aprender front-end com profundidade suficiente para criar e manter um produto profissional — sem transformar a UI no projeto inteiro.

## Decisões oficialmente adotadas

| Assunto | Decisão |
|---|---|
| Front-end | **Next.js (App Router) + React + TypeScript** |
| Aparência | **CSS Modules + CSS próprio**; sem framework visual pesado no início |
| API | **FastAPI/Python**, já implementada; preservar responsabilidades |
| Persistência | PostgreSQL + SQLAlchemy + Alembic |
| Integrações | MusicBrainz; uso de capas/faixas a avaliar por fonte e contrato |
| Testes atuais | **130 passed, 4 skipped, 1 warning** no PC do autor; suíte não foi reproduzida integralmente no ambiente de auditoria |
| Git | `main...origin/main` limpo; commit `0e7c598` ao receber o ZIP |
| Telas | 7 aprovadas; **Comunidade V1** como referência de trabalho, sem aceite final formal |
| Método | Uma funcionalidade de ponta a ponta por vez, com testes e checkpoint |

**Histórico de escolhas:** React+Vite e Vue+Vite foram hipóteses consideradas anteriormente; **foram substituídas pela decisão Next.js + React + TypeScript**. Não retomar a escolha do zero.

## Inventário de documentos deste pacote

1. `01_ARQUITETURA_E_REGRAS.md` — componentes, comunicação e decisões pendentes.
2. `02_MAPA_TELAS_E_API.md` — o que a API já oferece e o que depende de evolução.
3. `03_PLANO_DE_EXECUCAO.md` — ordem sugerida, definição de pronto e aprendizado.
4. `04_PROXIMA_SESSAO.md` — instruções curtas para iniciar outro dia.
5. `referencias/AUDITORIA_TECNICA_2026-11-12.md` — auditoria original do ZIP; note que sua proposta de React+Vite está **superada** por esta decisão.

**Fonte da verdade:** código e testes do repositório local/GitHub. Este material é planejamento e deve ser atualizado após mudanças relevantes.

## Fora de escopo hoje

- Não instalar pacotes nem criar o projeto Next.js agora.
- Não alterar o backend existente nem mover diretórios antigos.
- Não criar modelos visuais adicionais ou redefinir telas aprovadas.
- Não começar funcionalidades sociais avançadas antes dos fluxos principais.

## Princípios visuais V1

1. **Fluidez:** páginas contínuas, centralizadas, espaçamento natural, sem aparência de dashboard.
2. **Menos elementos, mais significado:** remover controles e explicações redundantes.
3. **Música protagonista:** capas, álbuns, reviews, avaliações.
4. **Identidade sem exageros:** claro/escuro, tipografia editorial, vermelho discreto.
5. **Experiência social evidente:** registro, avaliação, descoberta e discussão — nunca streaming.

**Referências favoritas internas:** Perfil e Detalhes de Lista (“Noite Indie”). Álbum é aprovado, com possíveis refinamentos futuros. A última Comunidade simplificada, sem banner, com feed e apoios discretos “Membros ativos”/“Em alta”, é apenas a referência para implementação, não uma demanda por mais mockups.

**Arquivos visuais:** estão preservados separadamente no ZIP `LETTERMUSIC_TELAS_REFERENCIA_2026-11-12.zip` da conversa. Não é preciso copiá-los para o repositório até decidir uma pasta de referência apropriada, e não devem ser confundidos com assets de produção.
