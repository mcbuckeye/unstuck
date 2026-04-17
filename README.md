# Unstuck

Mobile-first focus coaching web app for reducing procrastination and helping users start when they feel stuck.

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
- signup and login shell
- today screen
- task add + complete
- unstuck intervention flow
- sprint start + complete
- daily check-ins
- basic stats
- SQLAlchemy-backed persistence

## Deployment

The repo includes:
- `Dockerfile`
- `Dockerfile.frontend`
- `docker-compose.yml`

Designed for deployment via GitHub + Dokploy, but not deployed in this phase.
