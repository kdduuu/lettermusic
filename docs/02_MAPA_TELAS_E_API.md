# Lettermusic — Mapa de telas, API e prioridades V1

**Duas colunas diferentes:** uma tela estar **aprovada no desenho** não significa estar **implementada no código**. No ZIP de 12/11 não há front-end executável.

| Tela | Referência | API já existente | Lacuna a resolver durante integração |
|---|---|---|---|
| Descobrir | Aprovada | `/descoberta/mais-ouvidas`, `/descoberta/melhor-avaliadas`, busca | Capas, seções/filtros não presentes na API |
| Detalhe de álbum | Aprovada | busca, média, reviews por obra, interações | Dados completos do detalhe, capa, faixas; evitar dados fictícios |
| Perfil | Aprovada; favorita | `/usuarios/{username}`, `/usuarios/{username}/social` | Cinco **registros recentes** com capas, contagem coerente de registros e avatar |
| Reviews | Aprovada | publicar/editar/remover e reviews por obra | Listagem pública agregada, autor e metadados suficientes |
| Listas (explorar) | Aprovada | listas próprias e públicas por ID | Descoberta/listagem de listas públicas |
| Detalhes de lista | Aprovada; favorita | lista pública/privada e itens | Capas/colagens, autoria e consistência de metadados |
| Biblioteca | Aprovada | escutas, avaliações, favoritos, Quero ouvir | Composição real dos registros, capas e estados vazios |
| Comunidade | Referência V1, não aceite formal | mais ouvidas/melhores avaliadas; social por usuário | Feed global e consulta de membros com critérios reais |

## E as telas de apoio?

Login/cadastro, resultados de pesquisa, configurações mínimas e formulários/modais de edição são **fluxos essenciais**, mas não exigem novas rodadas longas de mockups. Projetá-los diretamente na implementação usando os tokens e componentes estabelecidos.

## Primeiro produto utilizável (núcleo da V1)

1. Usuário pesquisa um álbum real.
2. Entra no detalhe com dados realmente disponíveis.
3. Cria conta ou faz login.
4. Marca como ouvido, registra escuta, avalia ou escreve review respeitando regras da API.
5. Enxerga o resultado em Biblioteca.
6. Cria uma lista e adiciona/remove/reordena obras.
7. Visita um perfil público e encontra conteúdo real.

**Páginas públicas e Comunidade** vêm em seguida, criando somente endpoints que forem indispensáveis. Não precisamos de todos os recursos sociais avançados para comprovar os fluxos de ponta a ponta.

## Priorização

### Prioridade 0 — desbloquear uso real

- Fundação Next.js + estilos globais + navegação.
- Cliente HTTP centralizado, base URL configurável, estados de erro/carregamento/vazio.
- Busca + resultado real, detalhe de álbum mínimo e capa com fallback.
- Autenticação com estratégia segura decidida antes de persistir sessão.
- Escutas, avaliações, reviews, Biblioteca e listas com contratos já existentes.

### Prioridade 1 — completar as páginas públicas essenciais

- Listagem geral de reviews públicas com paginação e autor.
- Explorar listas públicas.
- Perfil: registros recentes, não ranking, e contagem fiel.
- Endpoint/agregação pública para o feed da Comunidade; pessoas com atividade recente, **não “online” sem presença real**.
- Detalhes e faixas de obra, condicionados à disponibilidade de fontes.

### Prioridade 2 — só se couber no escopo da primeira entrega

Curtidas, comentários, seguir usuários, notificações, upload de avatar, filtros sofisticados por gênero, recomendações personalizadas. Não deixar links ou ícones desses recursos fingindo funcionalidade; ocultar ou marcar claramente se forem futuros.

## Termos que não devem ser confundidos

- **Registro de escuta** ≠ **“Já ouvi”**.
- **Favorito** ≠ **Quero ouvir** ≠ **escuta**.
- **Média comunitária** ≠ **nota do usuário atual**.
- **Registros recentes do Perfil** ≠ **álbuns mais bem avaliados**.
- **Membros ativos** ≠ **usuários conectados agora**, salvo implementação de presença real.
- **Conteúdo ilustrativo do protótipo** ≠ **dados existentes da API**.

## Critério de validação por fluxo

Um fluxo estará concluído quando: (a) usar dados reais da API; (b) respeitar autorização e regras do backend; (c) mostrar carregamento, sucesso, erro e vazio; (d) funcionar após atualizar a página quando apropriado; (e) tiver teste ou procedimento reproduzível; (f) preservar padrão visual responsivo sem novas rodadas extensas de design.
