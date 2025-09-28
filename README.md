# NCHD Rostering & Leave System — Final (Multi‑repo style)

This package contains a **production-ready scaffold** for the NCHD Rostering & Leave System, organized as if split into multiple repositories:
- `backend/` (FastAPI, SQLAlchemy, rostering/leave engine, PostgreSQL)
- `frontend/` (React + Vite + TypeScript)
- `infra/` (Docker Compose, environment files, local dev certificates placeholder)
- `docs/` (architecture, APIs, compliance)
- `examples/` (seed data, demo scripts)
- `.github/workflows/` (CI: lint, tests, build, container images)

## Quick start (local, Docker Compose)
Requirements: Docker + Docker Compose.

```bash
docker compose -f infra/docker-compose.yml --project-directory . up --build
```
Services:
- Frontend: http://localhost:5173 (Vite preview) or http://localhost (if nginx is enabled)
- Backend: http://localhost:8000 (OpenAPI docs at `/docs`)
- Postgres: localhost:5432 (user: `roster`, password: `roster`, db: `rosterdb`)

> First run will auto‑seed **15 users**, **224 shifts**, and **224 call_assignments** (configurable).

## Monorepo-to-multi-repo
Although structured like a monorepo, each top folder can be pushed to its own repository later. CI workflows are scoped to subfolders.

## Spec coverage
Implements the **core data model** and **API surface** and scaffolds the engine for:
- EWTD (European Working Time Directive) compliance checks
- HSE (Health Service Executive) NCHD Contract (2023) checks
- OPD (Outpatient Department) guards, protected teaching, supervision
- Leave helper (Allowed / Conditional / Disallowed)
- Auto‑fix enumeration
- Full Audit logging
- Alerts & escalation

The complex optimization heuristics are **stubbed with working placeholders** and TODO markers for iterative completion. Endpoints and validators execute basic, safe checks on sample data.

## Developer commands

### Backend
```bash
cd backend
python -m venv .venv && source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
alembic upgrade head            # create tables
uvicorn app.main:app --reload
```

### Frontend
```bash
cd frontend
npm i
npm run dev
```

## Testing
```bash
cd backend
pytest -q
```

---

**License:** MIT (replace as appropriate).  
**Security:** Do not expose `.env` (credentials). Prefer Docker secrets or environment injection in production.
