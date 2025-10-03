# backend/app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import time
from sqlalchemy.exc import OperationalError

from .db import engine, Base, SessionLocal
from .seed import seed
from . import models  # ensure tables are registered

# Routers
from .routers import api as posts_api
from .routers import groups as groups_api
try:
    from .routers import solve  # optional
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

# Register routers (prefixes inside each router)
app.include_router(posts_api.router)    # /health, /posts
app.include_router(groups_api.router)   # /groups
if HAS_SOLVE:
    app.include_router(solve.router)    # /solve (if you have it)

@app.on_event("startup")
def on_startup():
    # retry for DB readiness (max ~30s)
    for _ in range(30):
        try:
            Base.metadata.create_all(bind=engine)  # for demo; prefer Alembic in prod
            break
        except OperationalError:
            time.sleep(1)
    else:
        Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        seed(db)
    finally:
        db.close()
