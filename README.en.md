# Lettermusic

[Leia em português](README.md)

A social music journal for discovering albums, logging listening activity, rating releases, writing reviews and sharing lists. Inspired by Album of the Year and Letterboxd, with an editorial interface. **Not a streaming service.**

**Status:** under development. The V1 editorial interface uses English. Functional validation and deployment are still pending.

## Stack

- Python 3.14, FastAPI, Pydantic, JWT and Argon2.
- PostgreSQL, SQLAlchemy, Psycopg and Alembic.
- Next.js 16, React, TypeScript and CSS Modules.
- MusicBrainz, Cover Art Archive and optional ListenBrainz popularity data.
- pytest, ESLint, TypeScript and GitHub Actions.

## Features

- Account creation, authentication, email verification and password recovery.
- Album, artist and track discovery.
- Listening history, ratings from 0.5 to 5 stars and editable reviews.
- Private favorites and listen-later collection.
- Paginated personal library, public and private lists, public profiles and community feed.

## Domain rules

Searches do not persist albums. Albums are stored on interaction and identified by MusicBrainz IDs. A user can have one listened marker, one rating and one review per album, with multiple listening events. The first rating or review logs a play; editing does not. Favoriting and adding to lists do not log a play. Private lists and personal account details are not exposed in public profiles.

The English interface does not change the existing API contracts, database schema or domain identifiers. User-generated content and music metadata retain their original language.

## Local setup

Install Python 3.14, PostgreSQL and Node.js 24. From the repository root (PowerShell):

```powershell
py -3.14 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

Copy `.env.example` to `.env`, configure PostgreSQL and set a strong `JWT_SECRET`. Keep credentials private.

```powershell
python -m alembic upgrade head
python -m uvicorn backend.app.main:app --reload
```

API: http://127.0.0.1:8000 — OpenAPI: http://127.0.0.1:8000/docs

In a separate terminal:

```powershell
cd frontend
npm ci
npm run dev
```

Frontend: http://localhost:3000. Server-side `BACKEND_URL` defaults to http://127.0.0.1:8000.

## Validation

```powershell
python -m pytest backend/tests -q
cd frontend
npm run lint
npx next typegen
npx tsc --noEmit
npm run build
```

See the [Portuguese README](README.md) for email, token cleanup and deployment configuration. Four PostgreSQL integration tests require `LETTERMUSIC_TEST_DATABASE_URL`.

## Before production

Configure HTTPS, secrets, email verification, shared rate limits, backups, logs, monitoring and privacy review. Run end-to-end tests. Do not deploy the development environment file.
