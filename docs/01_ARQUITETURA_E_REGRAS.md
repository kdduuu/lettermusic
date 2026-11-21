# Lettermusic — Arquitetura e regras da V1

## Fluxo principal

Navegador → Next.js → FastAPI → SQLAlchemy → PostgreSQL.

O FastAPI consulta o MusicBrainz e fontes auxiliares para
metadados. O Alembic controla alterações no banco.

## Responsabilidades

- Next.js: páginas, formulários e ações de apresentação.
- FastAPI: autenticação, autorização, validação e domínio.
- SQLAlchemy: acesso e transações do banco.
- PostgreSQL: persistência e integridade.
- Alembic: migrações versionadas.
- MusicBrainz: catálogo oficial de identificação.
- Cover Art Archive: capas quando disponíveis.
- ListenBrainz: popularidade opcional.

O navegador não recebe credenciais do PostgreSQL nem segredos.
O Next.js usa um cliente HTTP no servidor para falar com a API.

## Regras de domínio

1. Busca no MusicBrainz não cria automaticamente uma obra.
2. Obra passa a existir localmente quando houver interação.
3. Já ouvi é uma marcação única, diferente de múltiplas escutas.
4. Criar avaliação ou review registra uma escuta.
5. Editar avaliação ou review não gera escuta adicional.
6. Nota entre 0,5 e 5 em intervalos de 0,5.
7. Uma avaliação e uma review por usuário/obra.
8. Favoritos e Quero ouvir não registram escuta.
9. Listas privadas não são públicas, inclusive seus itens.
10. Apenas o dono modifica uma lista.
11. Exclusão de conta remove dados pessoais relacionados,
    sem apagar obras compartilhadas do catálogo.

## Segurança

- Senhas protegidas por hash Argon2.
- JWT com expiração e versão de sessão para revogação.
- Cookie HttpOnly no Next.js.
- Recuperação por token aleatório de uso único.
- Tokens armazenados como hashes e com prazo de expiração.
- Troca de senha invalida sessões e links pendentes.
- Confirmação de e-mail invalida links de confirmação restantes.
- Exclusão de conta exige senha atual.
- Limites locais para login, recuperação e cadastro.
- E-mail privado nunca incluído em perfis públicos.

## Limites conhecidos

Os limitadores atuais utilizam memória local. Na publicação,
será necessária proteção compartilhada ou equivalente.

O agendamento de limpeza de tokens não está ativo por padrão.
Há um comando administrativo de simulação e execução.

E-mails enviados por SMTP ainda dependem de configuração de
produção, monitoramento e testes de entregabilidade.

A documentação de publicação deverá tratar backup, recuperação,
exclusão de dados, abuso de conteúdo, logs e HTTPS.

## Escopo de catálogo

Não existe catálogo manual interno na V1. Obras ausentes devem
ser propostas ao MusicBrainz. Falhas temporárias de API devem
ser exibidas como indisponibilidade, não como obra inexistente.

## Escopo fora da V1

Streaming, chat, comentários, notificações, seguidores,
recomendações por IA e moderação administrativa complexa.
