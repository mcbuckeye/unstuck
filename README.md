# Unstuckinator

Mobile-first focus coaching web app for reducing procrastination and helping users start when they feel stuck.

**Website:** [unstuckinator.com](https://unstuckinator.com)

## Documents

- `PRD.md` — product requirements
- `BEHAVIOR_SYSTEM.md` — psychological model and intervention flows

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
- signup and login with JWT auth
- today screen
- task add + complete
- unstuck intervention flow
- sprint start + complete
- daily check-ins
- basic stats
- SQLAlchemy-backed persistence
- CORS configured for unstuckinator.com
- Alembic database migrations

## Deployment

The repo includes:
- `Dockerfile`
- `Dockerfile.frontend`
- `docker-compose.yml`

Designed for deployment via GitHub + Dokploy to unstuckinator.com, but not deployed in this phase.
