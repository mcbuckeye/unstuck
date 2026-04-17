# Pre-Deploy Checklist — Unstuckinator

Use this checklist before each production deployment.

## 1. Tests

- [ ] All 48 backend tests pass: `PYTHONPATH=. pytest tests/test_api.py -v`
- [ ] Full user journey test passes (signup → checkin → tasks → stuck → sprint → complete)
- [ ] Multi-user isolation test passes (no cross-user data leakage)
- [ ] Expired/tampered token tests pass
- [ ] Migration consistency test passes (ORM models match DB schema)
- [ ] All protected endpoints reject unauthenticated requests (sprints, checkins, unstuck)
- [ ] All validation edge cases covered (invalid mood, clarity, resistance, blank fields)
- [ ] Blocker-specific next_step mapping verified for all 6 blocker types

## 2. Configuration & Environment

- [ ] `JWT_SECRET` is set to a strong, unique value (not the dev default)
- [ ] `DATABASE_URL` points to the production PostgreSQL instance
- [ ] `JWT_EXPIRE_MINUTES` is set appropriately (default: 1440 = 24h)
- [ ] `.env.example` is up to date with all required variables
- [ ] No secrets are committed to the repo (check `.gitignore` covers `.env`)

## 3. Database & Migrations

- [ ] Alembic migration is current: `alembic upgrade head`
- [ ] Migration file matches ORM models (run `alembic check` or the test)
- [ ] Backup strategy is in place for the production database

## 4. Auth & Security

- [ ] JWT secret warning fires on startup if using dev default
- [ ] Passwords are hashed with bcrypt (never stored in plaintext)
- [ ] Signup response does not leak `password_hash` or `password`
- [ ] All protected endpoints reject missing/invalid/expired tokens
- [ ] CORS origins are correct for production domain

## 5. Docker & Deployment

- [ ] Backend Dockerfile builds cleanly: `docker build -f Dockerfile .`
- [ ] Backend Dockerfile runs `alembic upgrade head` before starting uvicorn
- [ ] Frontend Dockerfile builds production assets (not dev server)
- [ ] `docker-compose.yml` requires `JWT_SECRET` env var
- [ ] Health endpoint responds: `GET /api/health`

## 6. Frontend

- [ ] Error messages auto-dismiss after 5 seconds
- [ ] Empty states show helpful hints (tasks, interventions)
- [ ] Auth flow works end-to-end (signup → auto-login → dashboard)
- [ ] 401 responses clear token and redirect to login
- [ ] `vite.config.js` proxies `/api` to backend in dev mode

## Status

Last verified: 2026-04-17
