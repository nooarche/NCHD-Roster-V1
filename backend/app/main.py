# backend/app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

import time
from sqlalchemy.exc import OperationalError

from .db import engine, Base, SessionLocal
from .seed import seed
from . import models  # ensure models are imported so metadata knows all tables

# Routers
from .routers import api
from .routers import groups  # ANCHOR: GROUPS_ROUTER_IMPORT
try:
    # Optional: only include if you actually have backend/app/routers/solve.py
    from .routers import solve
    HAS_SOLVE = True
except Exception:
    HAS_SOLVE = False

app = FastAPI(title="NCHD Rostering & Leave System API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(api)
app.include_router(groups.router)
if HAS_SOLVE:
    app.include_router(solve.router)

@app.on_event("startup")
def on_startup():
    # Retry for DB readiness (max ~30s)
    for _ in range(30):
        try:
            Base.metadata.create_all(bind=engine)  # demo; Alembic preferred in prod
            break
        except OperationalError:
            time.sleep(1)
    else:
        # after 30 retries, re-raise so logs show the real failure
        Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        seed(db)
    finally:
        db.close()
