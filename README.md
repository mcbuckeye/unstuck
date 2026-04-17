# Unstuckinator

Mobile-first focus coaching web app for reducing procrastination and helping users start when they feel stuck.

**Website:** [unstuckinator.com](https://unstuckinator.com)

## Documents

- `PRD.md` — product requirements
- `BEHAVIOR_SYSTEM.md` — psychological model and intervention flows
- `PREDEPLOY_CHECKLIST.md` — pre-deploy verification checklist

## Development

### Backend
```bash
PYTHONPATH=. uvicorn backend.main:app --reload
```

### Frontend
```bash
cd frontend
npm install
npm run dev
```

### Tests
```bash
PYTHONPATH=. pytest tests/test_api.py
```

## Current MVP status

Implemented locally:
- Signup and login with JWT auth
- Today screen (dashboard with main focus, energy, wins, active sprint)
- Task add + complete
- Unstuck intervention flow (6 blocker types with specific guidance)
- Sprint start + complete (5/10/25 min)
- Daily check-ins (energy, mood, clarity, resistance)
- Stats dashboard (completed tasks, recovered stuck moments)
- SQLAlchemy-backed persistence with session-safe dependency injection
- CORS configured for unstuckinator.com
- Alembic database migrations (auto-run on Docker startup)
- 48 backend tests covering auth, validation, isolation, edge cases, and e2e journeys

## Environment Variables

Copy `.env.example` to `.env` and configure:

| Variable | Default | Description |
|---|---|---|
| `DATABASE_URL` | `sqlite:///./unstuck.db` | Database connection string |
| `JWT_SECRET` | dev default (must change for prod) | JWT signing secret |
| `JWT_EXPIRE_MINUTES` | `1440` | Token expiry in minutes |

## Deployment

The repo includes:
- `Dockerfile` — backend (Python/FastAPI)
- `Dockerfile.frontend` — frontend (React, production build served with `serve`)
- `docker-compose.yml` — orchestration (requires `JWT_SECRET` env var)
- `PREDEPLOY_CHECKLIST.md` — run through before each deploy

Designed for deployment via GitHub + Dokploy to unstuckinator.com, but not deployed in this phase.
