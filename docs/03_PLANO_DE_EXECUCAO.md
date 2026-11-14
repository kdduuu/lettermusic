# Lettermusic — Ordem de execução e forma de aprender

## Objetivo de ensino

Priorizar: **fluxo da requisição → contrato HTTP → regra de negócio → consulta/persistência → resposta → apresentação na tela**. O front-end será estudado com seriedade, mas o suficiente para desenvolver e manter a plataforma. Evitar gastar sessões inteiras lapidando CSS sem um fluxo de produto funcionando.

**Método de cada entrega:**

1. **Lógica:** o problema e a trajetória dos dados.
2. **Sintaxe:** quais arquivos, funções e componentes fazem isso.
3. **Motivo:** por que essa abordagem e quais alternativas foram descartadas.
4. **Aplicação:** executar, testar, conferir resultado e registrar.

## Ordem recomendada (não é cronograma em semanas)

### F01 — Fundação + primeiro acesso

- Verificar Node/npm, status Git e estrutura real do projeto.
- Criar o Next.js em `frontend/` com TypeScript + App Router + CSS Modules.
- Configurar tokens visuais mínimos (cores, fontes, espaçamentos) e cabeçalho baseado nas telas aprovadas.
- Criar cliente HTTP simples e checar `GET /health`/`GET /catalogo/buscar`.
- Tratar CORS para a origem real do Next.js.
- **Entrega observável:** navegador abre a interface e obtém resposta verdadeira da API, com tratamento de erro.

### F02 — Buscar álbum e abrir detalhe

- Construir busca com texto digitado, carregamento, erros e lista de resultados.
- Mostrar capa real quando houver e fallback quando não houver; evitar imagens de mockup como substituição silenciosa.
- Abrir página pública de detalhe com o que o backend já consegue entregar.
- **Complemento do backend apenas se necessário:** contrato de detalhe de obra.
- **Entrega observável:** um álbum real é pesquisável e navegável.

### F03 — Identidade + interações essenciais

- Definir estratégia de sessão e armazenamento de token antes de implementar login.
- Cadastro/login; marcar Já ouvi; registrar escuta; avaliar e review; favoritar/Quero ouvir.
- Ajustar estados e erros de autorização.
- **Entrega observável:** usuário autenticado consegue registrar música e reencontrar seus dados.

### F04 — Biblioteca + listas + perfil

- Renderizar Biblioteca sem confundir tipos de interação.
- Criar/editar/remover listas e reorganizar itens.
- Perfil público: corrigir exposição de registros recentes sem vazar dados privados.
- **Entrega observável:** registros e listas persistem e aparecem corretamente em páginas apropriadas.

### F05 — Descobrir + Reviews + Comunidade

- Completar endpoints públicos necessários: reviews gerais, explorar listas, feed público agregado.
- Integrar Membros ativos (baseados em atividades verdadeiras) e Em alta (rankings reais).
- Revisar experiências sociais essenciais, evitando recursos apenas decorativos.
- **Entrega observável:** navegar atividades públicas sem dados fictícios.

### F06 — Conclusão e publicação

- Responsividade essencial, revisão de acessibilidade e ações de teclado.
- Verificação de segurança, variáveis de ambiente, limites de abuso, logging e desempenho.
- Testar fluxos mais importantes de ponta a ponta; manter suíte Pytest/CI.
- Documentar execução local, deploy e decisões.
- **Entrega observável:** aplicação publicada, demonstrável e recuperável por outra pessoa.

## Regra para não virar um “projeto só de front-end”

- Uma tela isolada **não é uma entrega concluída** se não tiver funcionalidade ou se o dado estiver todo hardcoded.
- Não criar novos mockups por padrão; implementar diretamente componentes auxiliares de acordo com o design existente.
- Não fazer “grande reforma de backend” antes da integração. Cada contrato faltante entra junto do fluxo que o necessita, com teste.
- Não introduzir bibliotecas complexas antes de existir um motivo objetivo.
- Uma alteração pequena, uma validação, um commit claro: evitar substituir o projeto inteiro via ZIP sem necessidade.

## Definição de pronto da V1 (portfólio)

- [ ] Usuário consegue se cadastrar/autenticar de forma segura.
- [ ] Busca e navegação entre álbuns com dados reais.
- [ ] Escuta, Já ouvi, avaliação e review respeitam regras de negócio.
- [ ] Biblioteca e listas funcionam e preservam dados entre sessões.
- [ ] Perfil público, descoberta e páginas sociais mostram dados reais e autorização correta.
- [ ] Comunidade tem feed e seções com informações consistentes; sem funcionalidades falsas.
- [ ] Estados de erro/vazio/carregamento e responsividade nos principais fluxos.
- [ ] Testes relevantes de API e interfaces críticas, CI e documentação atualizada.
- [ ] Segredos fora do repo, configuração de publicação e backup/revisão de banco.

## Formato obrigatório do checkpoint ao fim de cada sessão

```markdown
### Checkpoint — data / sprint
**Objetivo:**
**Implementado:**
**Arquivos alterados:**
**Rotas/contratos usados:**
**Testes executados e resultados:**
**Decisões tomadas:**
**Pendências / riscos:**
**Próximo passo exato:**
**Git (branch/commit/status):**
```

Registrar resultado *real* dos testes, sem afirmar que passaram quando não foram executados.
