# Lettermusic — Frontend

Interface da plataforma social de música.

Stack: Next.js 16, React, TypeScript e CSS Modules.

## Desenvolvimento local

A partir da pasta `frontend`:

```powershell
npm ci
npm run dev
```

Acesse http://localhost:3000

O backend FastAPI precisa estar disponível no endereço
definido por `BACKEND_URL`, cujo padrão de desenvolvimento
é `http://127.0.0.1:8000`.

`BACKEND_URL` é utilizada pelo servidor Next.js.
Não coloque senhas ou JWT secrets em `NEXT_PUBLIC_*`.

## Verificações

```powershell
npm run lint
npm run build
npx tsc --noEmit
```

## Organização

- `src/app`: páginas, estilos e ações.
- `src/components`: componentes reutilizáveis.
- `src/lib`: consultas, contratos e sessão.
- `public`: recursos estáticos.

O FastAPI mantém a autoridade sobre regras de negócio,
autorização e persistência.

## Status

Funcionalmente implementado, aguardando refinamento
visual da F09 e validação pública da F10.
