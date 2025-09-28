
# Architecture

- **Backend**: FastAPI + SQLAlchemy + Alembic. Rostering engine stubs (`app/engine.py`) implement canonical shift definitions and initial EWTD checks. 
- **Frontend**: React (Vite). Simple demo UI with users list; dashboards for Admin/Supervisor/NCHD/Staff to be iteratively expanded.
- **Database**: PostgreSQL. See `migrations/versions/0001_init.py` for initial schema.
- **Infra**: Docker Compose for local dev. Replace with Kubernetes manifests as needed.

## Compliance
- EWTD and HSE Contract checks layered in validators. See TODOs for rolling averages and complex rest logic.
- Audit trail on all changes (extend via DB triggers or service middleware).

## API
OpenAPI at `/docs`. Key endpoints:
- `GET /health`
- `GET /users`, `POST /users`
- `POST /actions/roster-build`
- `POST /actions/roster-refresh`
